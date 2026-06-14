import { FormEvent, useEffect, useMemo, useState } from "react";

type IntegrationStatus = {
  configured: boolean;
  graphql_url: string;
};

type MeetingSummary = {
  keywords?: string[] | null;
  action_items?: string[] | null;
  outline?: string | null;
  shorthand_bullet?: string | null;
  overview?: string | null;
  bullet_gist?: string | null;
  gist?: string | null;
  short_summary?: string | null;
  short_overview?: string | null;
  meeting_type?: string | null;
  topics_discussed?: string[] | null;
};

type MeetingAttendee = {
  displayName?: string | null;
  email?: string | null;
  name?: string | null;
};

type TranscriptSentence = {
  index?: number | null;
  speaker_name?: string | null;
  text?: string | null;
  start_time?: number | null;
  end_time?: number | null;
};

type MeetingListItem = {
  id: string;
  title?: string | null;
  date?: number | null;
  dateString?: string | null;
  duration?: number | null;
  organizer_email?: string | null;
  host_email?: string | null;
  participants: string[];
  attendee_emails: string[];
  meeting_attendees: MeetingAttendee[];
  summary?: MeetingSummary | null;
  transcript_url?: string | null;
};

type MeetingDetail = MeetingListItem & {
  sentences: TranscriptSentence[];
};

type MeetingListResponse = {
  items: MeetingListItem[];
  limit: number;
  skip: number;
  has_more_hint: boolean;
};

type Filters = {
  keyword: string;
  scope: "title" | "sentences" | "all";
  fromDate: string;
  toDate: string;
  participants: string;
  organizers: string;
  mine: boolean;
};

const defaultFilters: Filters = {
  keyword: "",
  scope: "title",
  fromDate: "",
  toDate: "",
  participants: "",
  organizers: "",
  mine: false
};

export default function App() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingDetail | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    try {
      const currentStatus = await fetchJson<IntegrationStatus>("/api/integration/status");
      setStatus(currentStatus);
      if (currentStatus.configured) {
        await loadMeetings(defaultFilters);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function loadMeetings(nextFilters = filters) {
    setLoading(true);
    setError(null);
    setSelectedMeeting(null);
    setSelectedId(null);

    try {
      const response = await fetchJson<MeetingListResponse>(
        `/api/meetings?${buildSearchParams(nextFilters).toString()}`
      );
      setMeetings(response.items);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadMeetingDetail(meetingId: string) {
    setSelectedId(meetingId);
    setDetailLoading(true);
    setError(null);

    try {
      const meeting = await fetchJson<MeetingDetail>(`/api/meetings/${meetingId}`);
      setSelectedMeeting(meeting);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadMeetings(filters);
  }

  const selectedListItem = useMemo(
    () => meetings.find((meeting) => meeting.id === selectedId) ?? null,
    [meetings, selectedId]
  );

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">FastAPI + React</p>
          <h1>Fireflies meetings integration</h1>
          <p>
            Pull meetings from Fireflies.ai, inspect attendee emails, summaries, action
            items, and sentence-level call transcripts.
          </p>
        </div>
        <div className={status?.configured ? "status status-ok" : "status status-warn"}>
          {status?.configured ? "API key configured" : "Set FIREFLIES_API_KEY"}
        </div>
      </header>

      {!status?.configured && (
        <section className="notice">
          Add <code>FIREFLIES_API_KEY=...</code> to <code>.env</code> and restart the FastAPI
          server. The key stays on the backend and is never sent to the browser.
        </section>
      )}

      <section className="panel">
        <form className="filters" onSubmit={handleSubmit}>
          <label>
            Keyword
            <input
              value={filters.keyword}
              placeholder="Search title or transcript"
              onChange={(event) => setFilters({ ...filters, keyword: event.target.value })}
            />
          </label>
          <label>
            Scope
            <select
              value={filters.scope}
              onChange={(event) =>
                setFilters({ ...filters, scope: event.target.value as Filters["scope"] })
              }
            >
              <option value="title">Title</option>
              <option value="sentences">Transcript text</option>
              <option value="all">Title + transcript</option>
            </select>
          </label>
          <label>
            From
            <input
              type="datetime-local"
              value={filters.fromDate}
              onChange={(event) => setFilters({ ...filters, fromDate: event.target.value })}
            />
          </label>
          <label>
            To
            <input
              type="datetime-local"
              value={filters.toDate}
              onChange={(event) => setFilters({ ...filters, toDate: event.target.value })}
            />
          </label>
          <label>
            Participant emails
            <input
              value={filters.participants}
              placeholder="alice@company.com, bob@company.com"
              onChange={(event) => setFilters({ ...filters, participants: event.target.value })}
            />
          </label>
          <label>
            Organizer emails
            <input
              value={filters.organizers}
              placeholder="host@company.com"
              onChange={(event) => setFilters({ ...filters, organizers: event.target.value })}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.mine}
              onChange={(event) => setFilters({ ...filters, mine: event.target.checked })}
            />
            Only my meetings
          </label>
          <button disabled={loading} type="submit">
            {loading ? "Loading..." : "Load meetings"}
          </button>
        </form>
      </section>

      {error && <section className="error">{error}</section>}

      <section className="content-grid">
        <section className="panel meetings-panel">
          <div className="panel-heading">
            <h2>Meetings</h2>
            <span>{meetings.length} loaded</span>
          </div>
          <div className="meeting-list">
            {meetings.map((meeting) => (
              <button
                key={meeting.id}
                className={meeting.id === selectedId ? "meeting-card active" : "meeting-card"}
                onClick={() => loadMeetingDetail(meeting.id)}
                type="button"
              >
                <strong>{meeting.title || "Untitled meeting"}</strong>
                <span>{formatMeetingDate(meeting)}</span>
                <span>{formatDuration(meeting.duration)}</span>
                <small>{meeting.attendee_emails.length} attendee email(s)</small>
              </button>
            ))}
            {!loading && meetings.length === 0 && (
              <p className="empty">No meetings loaded yet. Adjust filters and click load.</p>
            )}
          </div>
        </section>

        <section className="panel detail-panel">
          <MeetingDetailView
            detailLoading={detailLoading}
            meeting={selectedMeeting}
            fallback={selectedListItem}
          />
        </section>
      </section>
    </main>
  );
}

function MeetingDetailView({
  detailLoading,
  meeting,
  fallback
}: {
  detailLoading: boolean;
  meeting: MeetingDetail | null;
  fallback: MeetingListItem | null;
}) {
  const current = meeting ?? fallback;

  if (detailLoading) {
    return <p className="empty">Loading transcript details...</p>;
  }

  if (!current) {
    return <p className="empty">Select a meeting to see summary and transcript.</p>;
  }

  const sentences = isMeetingDetail(current) ? current.sentences : [];

  return (
    <article>
      <div className="panel-heading">
        <div>
          <h2>{current.title || "Untitled meeting"}</h2>
          <p>{formatMeetingDate(current)}</p>
        </div>
        {current.transcript_url && (
          <a href={current.transcript_url} rel="noreferrer" target="_blank">
            Open in Fireflies
          </a>
        )}
      </div>

      <section className="detail-section">
        <h3>Attendee emails</h3>
        <ChipList values={current.attendee_emails} emptyText="No attendee emails returned." />
      </section>

      <section className="detail-section">
        <h3>Summary</h3>
        <Summary summary={current.summary} />
      </section>

      <section className="detail-section">
        <h3>Transcript</h3>
        {sentences.length > 0 ? (
          <div className="sentences">
            {sentences.map((sentence, index) => (
              <div className="sentence" key={`${sentence.index ?? index}-${sentence.start_time}`}>
                <span>{formatTimestamp(sentence.start_time)}</span>
                <div>
                  <strong>{sentence.speaker_name || "Unknown speaker"}</strong>
                  <p>{sentence.text}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty">Select the meeting or check whether Fireflies returned sentences.</p>
        )}
      </section>
    </article>
  );
}

function isMeetingDetail(meeting: MeetingListItem | MeetingDetail): meeting is MeetingDetail {
  return "sentences" in meeting && Array.isArray(meeting.sentences);
}

function Summary({ summary }: { summary?: MeetingSummary | null }) {
  if (!summary) {
    return <p className="empty">No summary returned.</p>;
  }

  return (
    <div className="summary-grid">
      <SummaryText title="Overview" value={summary.overview ?? summary.short_overview} />
      <SummaryText title="Short summary" value={summary.short_summary ?? summary.gist} />
      <SummaryText title="Bullet gist" value={summary.bullet_gist ?? summary.shorthand_bullet} />
      <SummaryList title="Action items" values={summary.action_items} />
      <SummaryList title="Topics discussed" values={summary.topics_discussed} />
      <SummaryList title="Keywords" values={summary.keywords} />
      {summary.meeting_type && (
        <div className="summary-block">
          <h4>Meeting type</h4>
          <p>{summary.meeting_type}</p>
        </div>
      )}
    </div>
  );
}

function SummaryText({ title, value }: { title: string; value?: string | null }) {
  if (!value) {
    return null;
  }

  return (
    <div className="summary-block">
      <h4>{title}</h4>
      <p>{value}</p>
    </div>
  );
}

function SummaryList({ title, values }: { title: string; values?: string[] | null }) {
  if (!values?.length) {
    return null;
  }

  return (
    <div className="summary-block">
      <h4>{title}</h4>
      <ul>
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}

function ChipList({ values, emptyText }: { values: string[]; emptyText: string }) {
  if (!values.length) {
    return <p className="empty">{emptyText}</p>;
  }

  return (
    <div className="chips">
      {values.map((value) => (
        <span key={value}>{value}</span>
      ))}
    </div>
  );
}

function buildSearchParams(filters: Filters) {
  const params = new URLSearchParams({ limit: "20", skip: "0" });

  if (filters.keyword.trim()) {
    params.set("keyword", filters.keyword.trim());
    params.set("scope", filters.scope);
  }
  appendIsoDate(params, "fromDate", filters.fromDate);
  appendIsoDate(params, "toDate", filters.toDate);
  appendCsvValues(params, "participants", filters.participants);
  appendCsvValues(params, "organizers", filters.organizers);
  if (filters.mine) {
    params.set("mine", "true");
  }

  return params;
}

function appendCsvValues(params: URLSearchParams, key: string, csv: string) {
  csv
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .forEach((value) => params.append(key, value));
}

function appendIsoDate(params: URLSearchParams, key: string, value: string) {
  if (!value) {
    return;
  }
  params.set(key, new Date(value).toISOString());
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = body?.detail ?? `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }

  return body as T;
}

function getErrorMessage(err: unknown) {
  return err instanceof Error ? err.message : "Unexpected error";
}

function formatMeetingDate(meeting: Pick<MeetingListItem, "date" | "dateString">) {
  if (meeting.dateString) {
    return meeting.dateString;
  }

  if (!meeting.date) {
    return "No date";
  }

  const timestamp = meeting.date > 100000000000 ? meeting.date : meeting.date * 1000;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(timestamp));
}

function formatDuration(duration?: number | null) {
  if (!duration) {
    return "Duration unknown";
  }

  const minutes = Math.round(duration / 60);
  return `${minutes} min`;
}

function formatTimestamp(seconds?: number | null) {
  if (seconds == null) {
    return "--:--";
  }

  const totalSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
