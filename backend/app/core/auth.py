from dataclasses import dataclass
from functools import lru_cache
import asyncio

import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthError, ConfigurationError, ExternalSourceError

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    id: str
    is_anonymous: bool
    role: str


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """JWKS를 한 번 로드하고 캐시. 재시작 시 갱신."""
    if not settings.supabase_url:
        raise ConfigurationError("인증에 필요한 SUPABASE_URL이 설정되지 않았습니다.")
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or not isinstance(data.get("keys"), list):
            raise ValueError("Invalid JWKS response")
        return data
    except (httpx.HTTPError, ValueError) as exc:
        raise ExternalSourceError("인증 서버의 서명 키를 가져오지 못했습니다. 연결 설정을 확인해 주세요.") from exc


async def verify_token(token: str) -> AuthUser:
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") not in {"RS256", "ES256"}:
            raise AuthError("지원하지 않는 인증 서명 방식입니다. Supabase 비대칭 서명 키 설정을 확인해 주세요.")
        if not header.get("kid"):
            raise AuthError("인증 토큰에 서명 키 식별자가 없습니다.")
        jwks = await asyncio.to_thread(_get_jwks)
        key = next((k for k in jwks["keys"] if k.get("kid") == header["kid"]), None)
        if key is None:
            # Refresh once on key rotation; never try an unrelated first key.
            _get_jwks.cache_clear()
            jwks = await asyncio.to_thread(_get_jwks)
            key = next((k for k in jwks["keys"] if k.get("kid") == header["kid"]), None)
        if not key:
            raise AuthError("인증 토큰의 서명 키를 찾지 못했습니다. 다시 로그인해 주세요.")

        payload = jwt.decode(
            token, key, algorithms=["RS256", "ES256"], audience="authenticated",
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
            options={"require_exp": True, "require_aud": True, "require_iss": True, "require_sub": True},
        )
        return AuthUser(
            id=payload["sub"],
            is_anonymous=payload.get("is_anonymous", False),
            role=payload.get("role", "authenticated"),
        )
    except (JWTError, KeyError, StopIteration, TypeError, ValueError) as exc:
        raise AuthError("인증 토큰이 유효하지 않거나 만료되었습니다. 다시 로그인해 주세요.") from exc


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser | None:
    if not creds:
        return None
    return await verify_token(creds.credentials)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    if not creds:
        raise AuthError()
    return await verify_token(creds.credentials)
