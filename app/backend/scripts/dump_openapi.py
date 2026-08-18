"""Write the app's OpenAPI schema to openapi.json.

The frontend generates its TypeScript types from this file, so the two ends
stop being two hand-maintained copies of the same shape.

    uv run python scripts/dump_openapi.py
"""

import json
import pathlib

from app.main import app

out = pathlib.Path(__file__).resolve().parent.parent / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"wrote {out.name}")
