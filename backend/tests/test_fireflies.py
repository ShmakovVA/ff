from backend.app.fireflies import LIST_TRANSCRIPTS_QUERY, _normalize_meeting
from backend.app.main import _split_query_values
from backend.app.schemas import MeetingDetail


def test_normalize_meeting_collects_email_sources() -> None:
    raw = {
        "id": "tr-1",
        "title": "Demo",
        "participants": ["HOST@example.com", " guest@example.com "],
        "meeting_attendees": [
            {"displayName": "Alex", "email": "alex@example.com"},
            {"displayName": "No Email"},
        ],
        "meeting_info": {"summary_status": "skipped", "silent_meeting": False},
        "summary": {
            "overview": "Quick update",
            "action_items": "Ship MVP",
            "keywords": ["Fireflies", "FastAPI"],
            "topics_discussed": None,
        },
        "sentences": [{"index": 0, "speaker_id": 1, "speaker_name": "Alex", "text": "Hello"}],
    }

    meeting = MeetingDetail.model_validate(_normalize_meeting(raw))

    assert meeting.attendee_emails == [
        "alex@example.com",
        "guest@example.com",
        "host@example.com",
    ]
    assert meeting.summary is not None
    assert meeting.summary.action_items == ["Ship MVP"]
    assert meeting.meeting_info is not None
    assert meeting.meeting_info.summary_status == "skipped"
    assert meeting.sentences[0].speaker_name == "Alex"
    assert meeting.sentences[0].speaker_id == 1


def test_split_query_values_accepts_repeated_and_comma_separated_values() -> None:
    assert _split_query_values(["a@example.com,b@example.com", "c@example.com"]) == [
        "a@example.com",
        "b@example.com",
        "c@example.com",
    ]


def test_transcripts_query_uses_fireflies_non_null_email_lists() -> None:
    assert "$organizers: [String!]" in LIST_TRANSCRIPTS_QUERY
    assert "$participants: [String!]" in LIST_TRANSCRIPTS_QUERY
