from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, HttpClientDep
from app.services.external_service import fetch_json_pair

router = APIRouter(prefix="/external", tags=["external"])


@router.get("/aggregate")
async def aggregate_external_data(
    http_client: HttpClientDep,
    current_user: CurrentUser,
    url_a: str = Query(min_length=8, max_length=500),
    url_b: str = Query(min_length=8, max_length=500),
):
    first, second = await fetch_json_pair(http_client, url_a, url_b)
    return {"data": {"first": first, "second": second}, "requested_by": current_user.id}
