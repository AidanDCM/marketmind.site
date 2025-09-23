#!/usr/bin/env python3
import os

try:
    import uvicorn
except ImportError as e:  # pragma: no cover
    raise SystemExit("uvicorn is required to run the API as a module. Install with `pip install uvicorn`.\n" + str(e))


def main() -> None:
    """Dev/staging launcher for the Hive API.

    Note: Production uses Gunicorn with Uvicorn workers (see Dockerfiles). This
    entrypoint is provided for convenience and for optional single-file packaging.
    """
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8001"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"

    uvicorn.run("apps.hive_api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
