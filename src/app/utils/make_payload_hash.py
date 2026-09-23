import datetime as dt
import hashlib
import json
from typing import Any
from uuid import UUID


def make_payload_hash(payload: dict[str, Any]) -> str:
    def default_serializer(obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, dt.datetime):
            return obj.isoformat()
        return str(obj)

    json_str = json.dumps(
        payload,
        sort_keys=True,
        default=default_serializer,
        separators=(',', ':'),
    )
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
