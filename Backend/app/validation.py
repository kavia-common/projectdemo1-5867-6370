import re
from datetime import datetime
from typing import Any, Dict, Tuple
from bson import ObjectId
from jsonschema import Draft7Validator, FormatChecker

# JSON Schema for device validation
DEVICE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Device",
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "ip_address": {"type": "string", "format": "ipv4"},
        "type": {"type": "string", "enum": ["router", "switch", "server"]},
        "location": {"type": "string", "maxLength": 200},
        "status": {"type": "string", "enum": ["online", "offline", "unknown"]},
        "last_checked": {"type": "string", "format": "date-time"},
    },
    "required": ["name", "ip_address", "type", "status"],
    "additionalProperties": False,
}

_format_checker = FormatChecker()

# Register a stricter IPv4 check (jsonschema ipv4 is acceptable; reinforce with regex)
_ipv4_regex = re.compile(
    r"^(25[0-5]|2[0-4]\d|1?\d?\d)\."
    r"(25[0-5]|2[0-4]\d|1?\d?\d)\."
    r"(25[0-5]|2[0-4]\d|1?\d?\d)\."
    r"(25[0-5]|2[0-4]\d|1?\d?\d)$"
)


@_format_checker.checks("ipv4")
def is_ipv4_format(value: str) -> bool:  # type: ignore[override]
    return isinstance(value, str) and _ipv4_regex.match(value) is not None


_validator = Draft7Validator(DEVICE_SCHEMA, format_checker=_format_checker)

# PUBLIC_INTERFACE
def validate_device_payload(payload: Dict[str, Any], partial: bool = False) -> Tuple[bool, Dict[str, str]]:
    """Validate a device payload against the JSON schema.

    Args:
        payload: The request JSON payload.
        partial: If True, does not enforce required fields (for updates).

    Returns:
        (is_valid, errors): A tuple indicating validity and a dict of field errors.
    """
    if partial:
        # For partial updates, relax required properties by cloning schema without 'required'
        schema = {k: v for k, v in DEVICE_SCHEMA.items()}
        schema.pop("required", None)
        validator = Draft7Validator(schema, format_checker=_format_checker)
    else:
        validator = _validator

    errors: Dict[str, str] = {}
    for err in validator.iter_errors(payload):
        path = ".".join([str(p) for p in err.path]) if err.path else "_root"
        errors[path] = err.message
    return (len(errors) == 0, errors)


# PUBLIC_INTERFACE
def to_object_id(id_str: str) -> ObjectId:
    """Convert a string to ObjectId, raising ValueError if invalid."""
    try:
        return ObjectId(id_str)
    except Exception as exc:
        raise ValueError("Invalid id format") from exc


# PUBLIC_INTERFACE
def serialize_device(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize a MongoDB document to a JSON-friendly dict (_id as string)."""
    if not doc:
        return doc
    out = {**doc}
    _id = out.get("_id")
    if _id is not None:
        out["_id"] = str(_id)
    # Ensure last_checked is isoformat if it's datetime
    lc = out.get("last_checked")
    if isinstance(lc, datetime):
        out["last_checked"] = lc.isoformat()
    return out
