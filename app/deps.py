# app/deps.py
import os
import hmac
import json
import hashlib
from typing import Optional, Dict
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException


def _validate_init_data(init_data: str, bot_token: str) -> Dict:
    if not init_data:
        raise HTTPException(
            status_code=401, detail="Missing Telegram initData"
        )

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(pairs.items(), key=lambda x: x[0])
    )

    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401, detail="Bad Telegram initData signature"
        )

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Missing user in initData")

    try:
        user = json.loads(user_raw)
    except Exception:
        raise HTTPException(
            status_code=401, detail="Bad user JSON in initData"
        )

    return {"pairs": pairs, "user": user}


def get_current_tg_user_id(
    authorization: Optional[str] = Header(default=None),
) -> int:
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Missing Authorization header"
        )

    if not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Bad Authorization scheme")

    init_data = authorization[4:].strip()
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise HTTPException(
            status_code=500,
            detail="Bot token is not configured (set BOT_TOKEN env var)",
        )

    data = _validate_init_data(init_data, bot_token)
    user_id = data["user"].get("id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Bad user id in initData")

    return user_id
