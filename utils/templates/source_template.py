"""
외부 API 클라이언트 템플릿.
복사 후 [SOURCE_NAME], [BASE_URL] 교체.
"""
import httpx
from app.core.exceptions import ExternalSourceError
from app.config import settings

_TIMEOUT = 8.0
_RETRIES = 2


async def fetch_items(param: str) -> list[dict]:
    """외부 API 조회 → 정규화 전 원본 응답 반환."""
    url = f"[BASE_URL]/endpoint"
    params = {
        "key": settings.topic_api_key,
        "param": param,
    }

    for attempt in range(_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json().get("items", [])
        except httpx.TimeoutException:
            if attempt == _RETRIES - 1:
                raise ExternalSourceError("[SOURCE_NAME] timeout")
        except httpx.HTTPStatusError as e:
            raise ExternalSourceError(f"[SOURCE_NAME] HTTP {e.response.status_code}")
        except Exception as e:
            # Raw exception strings may contain URLs with credentials or API keys.
            raise ExternalSourceError("[SOURCE_NAME] 조회에 실패했습니다. 연결 설정을 확인해 주세요.") from e

    return []
