from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint("Health", "health", url_prefix="/health", description="Health check route")


@blp.route("")
class HealthCheck(MethodView):
    """Basic health check endpoint returning status ok."""

    # PUBLIC_INTERFACE
    def get(self):
        """Returns a simple health marker for the service."""
        return {"status": "ok"}
