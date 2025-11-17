import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError
from .config import Config

_logger = logging.getLogger(__name__)


class Database:
    """Encapsulates MongoDB connection and collection access with index initialization."""

    def __init__(self, cfg: Config):
        self._cfg = cfg
        try:
            self._client = MongoClient(cfg.mongodb_uri, serverSelectionTimeoutMS=3000)
            # Validate connection early (fail fast)
            self._client.admin.command("ping")
        except Exception as e:
            _logger.exception("Failed to connect to MongoDB: %s", e)
            raise
        self._db = self._client[cfg.mongodb_db_name]
        self._collection = self._db[cfg.mongodb_collection_name]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create indexes idempotently (unique on ip_address, and on name, status)."""
        try:
            self._collection.create_index([("ip_address", ASCENDING)], name="uniq_ip", unique=True)
            self._collection.create_index([("name", ASCENDING)], name="idx_name")
            self._collection.create_index([("status", ASCENDING)], name="idx_status")
            _logger.info("MongoDB indexes ensured (uniq_ip, idx_name, idx_status).")
        except PyMongoError as e:
            _logger.exception("Failed ensuring MongoDB indexes: %s", e)
            raise

    # PUBLIC_INTERFACE
    def collection(self):
        """Return the devices collection."""
        return self._collection
