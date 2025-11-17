# Network Device Management Backend (Flask)

This Flask backend provides RESTful APIs to manage network devices with MongoDB persistence. It supports device CRUD operations, optional ping-based status checks, input validation, and OpenAPI documentation.

## Features

- REST API for devices:
  - GET /health
  - GET /devices (optional query by `status` and `name`)
  - POST /devices
  - GET /devices/<id>
  - PUT /devices/<id>
  - DELETE /devices/<id>
  - POST /devices/<id>/ping
- MongoDB integration via `pymongo`
- Idempotent MongoDB indexes:
  - Unique index on `ip_address`
  - Index on `name`
  - Index on `status`
- Request payload validation with JSON Schema
- Structured JSON errors and logging
- OpenAPI docs at `/docs`

## Requirements

- Python 3.10+
- A reachable MongoDB instance
- Environment variables configured (see `.env.example`)

## Environment Variables

- `MONGODB_URI` (required): MongoDB connection string.
- `MONGODB_DB_NAME` (optional, default `network_devices`): Database name.
- `MONGODB_COLLECTION_NAME` (optional, default `devices`): Collection name.
- `PORT` (optional, default `3001`): Port for the Flask app. The preview system uses 3001.

See `.env.example` for a template.

## Running Locally

1. Create and activate a virtual environment.
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set required environment variables (e.g., via `.env` or your shell):

   ```
   export MONGODB_URI="mongodb://localhost:27017"
   export MONGODB_DB_NAME="network_devices"
   export MONGODB_COLLECTION_NAME="devices"
   export PORT=3001
   ```

4. Start the server:

   ```
   python run.py
   ```

OpenAPI documentation is available at:
- Swagger UI: `http://localhost:3001/docs/`
- OpenAPI JSON: `http://localhost:3001/openapi.json`

## Payload Validation

Schema constraints:
- `name`: string, 1..100 chars
- `ip_address`: string, IPv4 format
- `type`: one of `router`, `switch`, `server`
- `location`: optional string, max 200 chars
- `status`: one of `online`, `offline`, `unknown`
- `last_checked`: optional ISO 8601 date-time string

Additional properties are rejected.

## Ping Endpoint

- `POST /devices/<id>/ping`: Pings the device IP.
  - Updates `status` to `online` or `offline` and sets `last_checked` to an ISO timestamp.
  - If the `ping` command is not available or not permitted, returns `note=ping-not-available` and sets status to `unknown`.

## Error Responses

- 400 Validation error: `{ "code":400, "status":"Bad Request", "message": "...", "errors": {...} }`
- 404 Not found
- 409 Duplicate `ip_address`
- 500 Server or database error

## Notes

- All responses normalize `_id` to a string.
- Indexes are created at startup and are idempotent.

## Development

- The app uses `flask-smorest` for API docs and error helpers.
- Code layout:
  ```
  app/
    __init__.py        # app factory, API registration, error handlers
    config.py          # env-based configuration
    db.py              # MongoDB client and indexes
    validation.py      # JSON schema and validators
    ping_util.py       # platform-aware ping
    routes/
      health.py
      devices.py
  run.py
  ```

## Troubleshooting

- Missing `MONGODB_URI` will cause startup failure with a clear error message.
- Ensure MongoDB is reachable; the app performs a connection ping at startup.
- If `ping` is not available in your environment, the `/ping` endpoint will return a note and set device status to `unknown`.
