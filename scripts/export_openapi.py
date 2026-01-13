import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.index import app

openapi_schema = app.openapi()

with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)
