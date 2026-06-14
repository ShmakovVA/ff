# Fireflies meetings integration

FastAPI + React application for integrating with the Fireflies.ai GraphQL API and reading:

- meeting list and meeting details;
- attendee emails from `participants` and `meeting_attendees`;
- AI summary fields such as overview, topics, keywords, and action items;
- sentence-level transcript with speaker names and timestamps.

## Fireflies API notes

Fireflies exposes a GraphQL endpoint at:

```text
https://api.fireflies.ai/graphql
```

Authentication is done with:

```text
Authorization: Bearer <FIREFLIES_API_KEY>
```

The app uses:

- `transcripts(...)` to load meetings with filters by keyword, date range, organizers, participants, and `mine`;
- `transcript(id: ...)` to load a selected meeting with `sentences`;
- fields `participants`, `meeting_attendees`, `summary`, and `sentences` to build the UI.

## Setup

Install dependencies:

```bash
uv sync
npm install
```

Create local environment:

```bash
cp .env.example .env
```

Then set:

```text
FIREFLIES_API_KEY=...
```

## Run

Backend:

```bash
make backend
```

Frontend:

```bash
make frontend
```

Open the Vite URL, normally `http://localhost:5173`.

## Verify

```bash
make test
```

This runs backend tests and the React production build.