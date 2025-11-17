import os
from app import app

if __name__ == "__main__":
    # Respect existing preview port (3001). Allow PORT override but default to 3001.
    port = int(os.getenv("PORT", "3001"))
    # Bind to all interfaces for containerized preview
    app.run(host="0.0.0.0", port=port)
