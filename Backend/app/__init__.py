import logging
from logging import StreamHandler
from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api

from .config import Config
from .db import Database
from .routes.health import blp as health_blp
from .routes.devices import blp as devices_blp

# Flask app setup
app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenAPI / Docs config
app.config["API_TITLE"] = "Network Device Management API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Logging
_handler = StreamHandler()
_handler.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger(__name__)

# Load config and init DB (fail fast if invalid)
try:
    _config = Config.from_env()
except Exception as e:
    # Note: Raising here will cause the app to fail to start in CI if env missing
    logger.exception("Configuration error on startup: %s", e)
    # In some preview systems, import-time exceptions may be swallowed; still raise.
    raise

# Global db instance for routes to import as needed
db_instance = Database(_config)

# API / blueprints
api = Api(app)
api.register_blueprint(health_blp)
api.register_blueprint(devices_blp)


# Error handlers for structured JSON responses
@app.errorhandler(400)
def handle_400(err):
    payload = getattr(err, "data", None)
    errors = payload.get("errors") if isinstance(payload, dict) else None
    return jsonify({"code": 400, "status": "Bad Request", "message": getattr(err, "description", "Bad Request"), "errors": errors}), 400


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"code": 404, "status": "Not Found", "message": getattr(err, "description", "Not Found")}), 404


@app.errorhandler(409)
def handle_409(err):
    return jsonify({"code": 409, "status": "Conflict", "message": getattr(err, "description", "Conflict")}), 409


@app.errorhandler(500)
def handle_500(err):
    return jsonify({"code": 500, "status": "Internal Server Error", "message": getattr(err, "description", "Internal Server Error")}), 500
