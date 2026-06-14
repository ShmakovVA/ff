from collections.abc import Iterable
from typing import Any

import httpx

from .config import Settings
from .schemas import MeetingDetail, MeetingListItem, MeetingSummary


TRANSCRIPT_FIELDS = """
  id
  title
  dateString
  host_email
  organizer_email
  participants
  date
  transcript_url
  audio_url
  video_url
  duration
  meeting_attendees {
    displayName
    email
    phoneNumber
    name
    location
  }
  meeting_info {
    fred_joined
    silent_meeting
    summary_status
  }
  summary {
    keywords
    action_items
    outline
    shorthand_bullet
    overview
    bullet_gist
    gist
    short_summary
    short_overview
    meeting_type
    topics_discussed
    transcript_chapters
  }
"""


LIST_TRANSCRIPTS_QUERY = f"""
query Transcripts(
  $keyword: String
  $scope: String
  $fromDate: DateTime
  $toDate: DateTime
  $limit: Int
  $skip: Int
  $organizers: [String!]
  $participants: [String!]
  $mine: Boolean
) {{
  transcripts(
    keyword: $keyword
    scope: $scope
    fromDate: $fromDate
    toDate: $toDate
    limit: $limit
    skip: $skip
    organizers: $organizers
    participants: $participants
    mine: $mine
  ) {{
    {TRANSCRIPT_FIELDS}
  }}
}}
"""


GET_TRANSCRIPT_QUERY = f"""
query Transcript($transcriptId: String!) {{
  transcript(id: $transcriptId) {{
    {TRANSCRIPT_FIELDS}
    sentences {{
      index
      speaker_name
      speaker_id
      text
      raw_text
      start_time
      end_time
    }}
  }}
}}
"""


class FirefliesAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class FirefliesNotConfiguredError(FirefliesAPIError):
    def __init__(self) -> None:
        super().__init__(
            "FIREFLIES_API_KEY is not configured on the backend.",
            status_code=503,
        )


class FirefliesClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def list_transcripts(
        self,
        *,
        keyword: str | None,
        scope: str | None,
        from_date: str | None,
        to_date: str | None,
        limit: int,
        skip: int,
        organizers: list[str] | None,
        participants: list[str] | None,
        mine: bool | None,
    ) -> list[MeetingListItem]:
        variables = {
            "keyword": keyword,
            "scope": scope,
            "fromDate": from_date,
            "toDate": to_date,
            "limit": limit,
            "skip": skip,
            "organizers": organizers,
            "participants": participants,
            "mine": mine,
        }
        data = await self._graphql(LIST_TRANSCRIPTS_QUERY, variables)
        transcripts = data.get("transcripts") or []
        return [MeetingListItem.model_validate(_normalize_meeting(item)) for item in transcripts]

    async def get_transcript(self, transcript_id: str) -> MeetingDetail:
        data = await self._graphql(GET_TRANSCRIPT_QUERY, {"transcriptId": transcript_id})
        transcript = data.get("transcript")
        if not transcript:
            raise FirefliesAPIError("Transcript was not found or is not accessible.", status_code=404)
        return MeetingDetail.model_validate(_normalize_meeting(transcript))

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if not self._settings.fireflies_api_key:
            raise FirefliesNotConfiguredError()

        payload = {
            "query": query,
            "variables": {key: value for key, value in variables.items() if value is not None},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.fireflies_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self._settings.request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self._settings.fireflies_graphql_url,
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise FirefliesAPIError(f"Fireflies request failed: {exc}") from exc

        if response.status_code >= 400:
            raise FirefliesAPIError(
                f"Fireflies returned HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        body = response.json()
        errors = body.get("errors")
        if errors:
            message = "; ".join(error.get("message", "Unknown GraphQL error") for error in errors)
            raise FirefliesAPIError(f"Fireflies GraphQL error: {message}")

        return body.get("data") or {}


def _normalize_meeting(raw: dict[str, Any]) -> dict[str, Any]:
    item = dict(raw)
    item["participants"] = _coerce_string_list(item.get("participants"))
    item["meeting_attendees"] = item.get("meeting_attendees") or []
    item["attendee_emails"] = _collect_attendee_emails(item)

    if item.get("summary"):
        item["summary"] = _normalize_summary(item["summary"])
    if item.get("sentences"):
        item["sentences"] = item["sentences"] or []
    return item


def _normalize_summary(raw: dict[str, Any]) -> dict[str, Any]:
    summary = dict(raw)
    for field_name in ("keywords", "action_items", "topics_discussed"):
        summary[field_name] = _coerce_string_list(summary.get(field_name))
    return MeetingSummary.model_validate(summary).model_dump()


def _collect_attendee_emails(item: dict[str, Any]) -> list[str]:
    emails = list(_coerce_string_list(item.get("participants")))
    for attendee in item.get("meeting_attendees") or []:
        email = (attendee or {}).get("email")
        if email:
            emails.append(str(email))
    return sorted({email.strip().lower() for email in emails if email and email.strip()})


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    return [str(value)]
