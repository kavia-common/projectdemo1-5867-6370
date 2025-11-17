import os
import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""
    mongodb_uri: str
    mongodb_db_name: str
    mongodb_collection_name: str

    @staticmethod
    # PUBLIC_INTERFACE
    def from_env() -> "Config":
        """Create configuration from environment variables with defaults and validation.

        Returns:
            Config: Application configuration.

        Raises:
            ValueError: If required environment variables are missing or invalid.
        """
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError(
                "Missing required environment variable MONGODB_URI. "
                "Set it to your MongoDB connection string."
            )
        mongodb_db_name = os.getenv("MONGODB_DB_NAME", "network_devices")
        mongodb_collection_name = os.getenv("MONGODB_COLLECTION_NAME", "devices")

        # Basic sanity checks
        if not isinstance(mongodb_db_name, str) or not mongodb_db_name.strip():
            raise ValueError("MONGODB_DB_NAME must be a non-empty string.")
        if not isinstance(mongodb_collection_name, str) or not mongodb_collection_name.strip():
            raise ValueError("MONGODB_COLLECTION_NAME must be a non-empty string.")

        logging.getLogger(__name__).info(
            "Config loaded. DB=%s, Collection=%s", mongodb_db_name, mongodb_collection_name
        )
        return Config(
            mongodb_uri=mongodb_uri,
            mongodb_db_name=mongodb_db_name,
            mongodb_collection_name=mongodb_collection_name,
        )
