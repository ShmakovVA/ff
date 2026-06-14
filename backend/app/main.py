from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .fireflies import FirefliesAPIError, FirefliesClient
from .schemas import IntegrationStatus, MeetingDetail, MeetingListResponse


app = FastAPI(
    title="Fireflies Meetings Integration",
    description="FastAPI gateway for reading Fireflies meetings, attendees, transcripts, and summaries.",
    version="0.1.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client(settings: Annotated[Settings, Depends(get_settings)]) -> FirefliesClient:
    return FirefliesClient(settings)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/integration/status", response_model=IntegrationStatus)
async def integration_status(settings: Annotated[Settings, Depends(get_settings)]) -> IntegrationStatus:
    return IntegrationStatus(
        configured=bool(settings.fireflies_api_key),
        graphql_url=settings.fireflies_graphql_url,
    )


@app.get("/api/meetings", response_model=MeetingListResponse)
async def list_meetings(
    client: Annotated[FirefliesClient, Depends(get_client)],
    keyword: Annotated[str | None, Query(max_length=255)] = None,
    scope: Annotated[str | None, Query(pattern="^(title|sentences|all)$")] = None,
    from_date: Annotated[str | None, Query(alias="fromDate")] = None,
    to_date: Annotated[str | None, Query(alias="toDate")] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    skip: Annotated[int, Query(ge=0)] = 0,
    organizers: Annotated[list[str] | None, Query()] = None,
    participants: Annotated[list[str] | None, Query()] = None,
    mine: bool | None = None,
) -> MeetingListResponse:
    try:
        items = await client.list_transcripts(
            keyword=keyword,
            scope=scope,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            skip=skip,
            organizers=_split_query_values(organizers),
            participants=_split_query_values(participants),
            mine=mine,
        )
    except FirefliesAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return MeetingListResponse(
        items=items,
        limit=limit,
        skip=skip,
        has_more_hint=len(items) == limit,
    )


@app.get("/api/meetings/{transcript_id}", response_model=MeetingDetail)
async def get_meeting(
    transcript_id: str,
    client: Annotated[FirefliesClient, Depends(get_client)],
) -> MeetingDetail:
    try:
        return await client.get_transcript(transcript_id)
    except FirefliesAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def _split_query_values(values: list[str] | None) -> list[str] | None:
    if not values:
        return None

    flattened: list[str] = []
    for value in values:
        flattened.extend(part.strip() for part in value.split(",") if part.strip())
    return flattened or None
