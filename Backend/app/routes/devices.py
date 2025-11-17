import logging
from datetime import datetime, timezone
from typing import Any, Dict

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from pymongo.errors import DuplicateKeyError, PyMongoError

from ..db import Database
from ..validation import validate_device_payload, serialize_device, to_object_id
from ..ping_util import ping_host

logger = logging.getLogger(__name__)

blp = Blueprint(
    "Devices",
    "devices",
    url_prefix="/devices",
    description="Device CRUD and status operations",
)


def _get_db() -> Database:
    from .. import db_instance  # imported at runtime from app.__init__
    return db_instance


@blp.route("")
class DevicesList(MethodView):
    """List and create devices."""

    # PUBLIC_INTERFACE
    def get(self):
        """List all devices with optional query params: status, name (substring match)."""
        coll = _get_db().collection()
        query: Dict[str, Any] = {}
        status = request.args.get("status")
        name = request.args.get("name")
        if status:
            query["status"] = status
        if name:
            # Case-insensitive partial match on name
            query["name"] = {"$regex": name, "$options": "i"}
        try:
            items = [serialize_device(doc) for doc in coll.find(query).sort("name", 1)]
            return {"data": items, "count": len(items)}, 200
        except PyMongoError as e:
            logger.exception("DB error on list: %s", e)
            abort(500, message="Database error")

    # PUBLIC_INTERFACE
    def post(self):
        """Create a new device with JSON body validation."""
        payload = request.get_json(silent=True) or {}
        ok, errors = validate_device_payload(payload, partial=False)
        if not ok:
            abort(400, message="Validation failed", errors=errors)

        # Normalize payload for insert
        doc: Dict[str, Any] = {
            "name": payload["name"],
            "ip_address": payload["ip_address"],
            "type": payload["type"],
            "status": payload["status"],
        }
        if "location" in payload:
            doc["location"] = payload["location"]
        if "last_checked" in payload:
            # allow client provided ISO datetime if valid - stored as string or datetime? Keep as ISO string to match schema
            doc["last_checked"] = payload["last_checked"]

        coll = _get_db().collection()
        try:
            res = coll.insert_one(doc)
            created = coll.find_one({"_id": res.inserted_id})
            return {"data": serialize_device(created)}, 201
        except DuplicateKeyError:
            abort(409, message="Device with the same ip_address already exists")
        except PyMongoError as e:
            logger.exception("DB error on create: %s", e)
            abort(500, message="Database error")


@blp.route("/<string:item_id>")
class DeviceDetail(MethodView):
    """Get, update, delete a device by id."""

    # PUBLIC_INTERFACE
    def get(self, item_id: str):
        """Get a single device by its id."""
        try:
            oid = to_object_id(item_id)
        except ValueError:
            abort(400, message="Invalid id")

        coll = _get_db().collection()
        try:
            doc = coll.find_one({"_id": oid})
            if not doc:
                abort(404, message="Device not found")
            return {"data": serialize_device(doc)}, 200
        except PyMongoError as e:
            logger.exception("DB error on read: %s", e)
            abort(500, message="Database error")

    # PUBLIC_INTERFACE
    def put(self, item_id: str):
        """Update a device by its id with JSON body validation."""
        try:
            oid = to_object_id(item_id)
        except ValueError:
            abort(400, message="Invalid id")

        payload = request.get_json(silent=True) or {}
        ok, errors = validate_device_payload(payload, partial=True)
        if not ok:
            abort(400, message="Validation failed", errors=errors)
        if not payload:
            abort(400, message="No fields provided for update")

        coll = _get_db().collection()
        try:
            result = coll.update_one({"_id": oid}, {"$set": payload})
            if result.matched_count == 0:
                abort(404, message="Device not found")
            doc = coll.find_one({"_id": oid})
            return {"data": serialize_device(doc)}, 200
        except DuplicateKeyError:
            abort(409, message="Device with the same ip_address already exists")
        except PyMongoError as e:
            logger.exception("DB error on update: %s", e)
            abort(500, message="Database error")

    # PUBLIC_INTERFACE
    def delete(self, item_id: str):
        """Delete a device by its id."""
        try:
            oid = to_object_id(item_id)
        except ValueError:
            abort(400, message="Invalid id")

        coll = _get_db().collection()
        try:
            res = coll.delete_one({"_id": oid})
            if res.deleted_count == 0:
                abort(404, message="Device not found")
            return {"message": "Deleted"}, 200
        except PyMongoError as e:
            logger.exception("DB error on delete: %s", e)
            abort(500, message="Database error")


@blp.route("/<string:item_id>/ping", methods=["POST"])
class DevicePing(MethodView):
    """Ping a device by id and update its status/last_checked."""

    # PUBLIC_INTERFACE
    def post(self, item_id: str):
        """Ping device and update status to online/offline, last_checked to now.

        Returns 'unknown' if ping is not available in environment.
        """
        try:
            oid = to_object_id(item_id)
        except ValueError:
            abort(400, message="Invalid id")

        coll = _get_db().collection()
        doc = coll.find_one({"_id": oid})
        if not doc:
            abort(404, message="Device not found")

        ip = doc.get("ip_address")
        reachable, note = ping_host(ip, timeout_seconds=2)

        if note == "ping-not-available":
            # Gracefully return unknown without updating status unless explicitly desired
            updated = {"status": "unknown", "last_checked": datetime.now(timezone.utc).isoformat()}
            coll.update_one({"_id": oid}, {"$set": updated})
            refreshed = coll.find_one({"_id": oid})
            return {"data": serialize_device(refreshed), "note": "ping-not-available"}, 200

        new_status = "online" if reachable else "offline"
        updated = {"status": new_status, "last_checked": datetime.now(timezone.utc).isoformat()}
        try:
            coll.update_one({"_id": oid}, {"$set": updated})
            refreshed = coll.find_one({"_id": oid})
            return {"data": serialize_device(refreshed), "note": note}, 200
        except PyMongoError as e:
            logger.exception("DB error on ping update: %s", e)
            abort(500, message="Database error")
