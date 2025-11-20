from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.config import get_settings


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    settings = get_settings()
    expiry = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expiry).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY or "fallback-secret", algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY or "fallback-secret", algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None

