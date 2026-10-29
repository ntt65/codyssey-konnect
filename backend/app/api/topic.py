"""Topic API router.

Provides a simple discovery endpoint that returns a list of Candidate objects
wrapped in a DiscoverResponse. This is a placeholder implementation – in a real
project you would replace the dummy data with calls to your RAG / LLM pipeline.
"""

from fastapi import APIRouter
from app.models.topic import DiscoverRequest, DiscoverResponse, Candidate, ResultStatus
from app.models.common import Envelope

router = APIRouter(prefix="/api/topic", tags=["Topic"])

@router.post("/discover", response_model=Envelope[DiscoverResponse])
def discover(request: DiscoverRequest) -> Envelope[DiscoverResponse]:
    """Return a static example response.

    Args:
        request: The incoming request containing a search query and optional
            pagination parameters.
    Returns:
        DiscoverResponse with a single dummy Candidate.
    """
    dummy_candidate = Candidate(
        id="c1",
        name="Sample",
        description="Sample description",
        status=ResultStatus.CONFIRMED,
        price="free",
        location="Seoul",
    )
    return Envelope.ok_response(DiscoverResponse(candidates=[dummy_candidate], total=1))
