from typing import Any

from pydantic import BaseModel, Field


class MeetingAttendee(BaseModel):
    display_name: str | None = Field(default=None, alias="displayName")
    email: str | None = None
    phone_number: str | None = Field(default=None, alias="phoneNumber")
    name: str | None = None
    location: str | None = None


class MeetingSummary(BaseModel):
    keywords: list[str] | None = None
    action_items: list[str] | None = None
    outline: str | None = None
    shorthand_bullet: str | None = None
    overview: str | None = None
    bullet_gist: str | None = None
    gist: str | None = None
    short_summary: str | None = None
    short_overview: str | None = None
    meeting_type: str | None = None
    topics_discussed: list[str] | None = None
    transcript_chapters: list[Any] | None = None


class MeetingInfo(BaseModel):
    fred_joined: bool | None = None
    silent_meeting: bool | None = None
    summary_status: str | None = None


class TranscriptSentence(BaseModel):
    index: int | None = None
    speaker_name: str | None = None
    speaker_id: str | int | None = None
    text: str | None = None
    raw_text: str | None = None
    start_time: float | None = None
    end_time: float | None = None


class MeetingListItem(BaseModel):
    id: str
    title: str | None = None
    date: float | None = None
    date_string: str | None = Field(default=None, alias="dateString")
    duration: float | None = None
    organizer_email: str | None = None
    host_email: str | None = None
    participants: list[str] = Field(default_factory=list)
    attendee_emails: list[str] = Field(default_factory=list)
    meeting_attendees: list[MeetingAttendee] = Field(default_factory=list)
    meeting_info: MeetingInfo | None = None
    summary: MeetingSummary | None = None
    transcript_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None


class MeetingDetail(MeetingListItem):
    sentences: list[TranscriptSentence] = Field(default_factory=list)


class MeetingListResponse(BaseModel):
    items: list[MeetingListItem]
    limit: int
    skip: int
    has_more_hint: bool


class IntegrationStatus(BaseModel):
    configured: bool
    graphql_url: str
