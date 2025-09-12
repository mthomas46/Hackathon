# Report Examples

## Life of the Ticket (Markdown)

# Life of the Ticket Report (Example)

## Issue
- **Key**: HELLO-2
- **Summary**: Create Hello World Service
- **Description**: As a user, I can GET /hello to receive 'hello world'
- **Type**: Story
- **Project**: HELLO

## Timeline
- 2025-01-01T08:00:00Z — jira — status_change — Status change: To Do -> In Progress
- 2025-01-01T09:00:00Z — jira — comment — Starting implementation for /hello (Dev A)
- 2025-01-01T15:30:00Z — jira — comment — Add unit tests and docs. (Dev B)
- 2025-01-01T17:45:00Z — jira — comment — Is this ready for PR by standup tomorrow? (Scrum Master)
- 2025-01-02T10:05:00Z — jira — comment — PR opened: please review. (Dev A)
- 2025-01-02T12:10:00Z — github — pr — Add hello endpoint and tests (#42)
- 2025-01-02T12:11:00Z — github — file — app/main.py
- 2025-01-02T12:11:00Z — github — file — tests/test_hello.py
- 2025-01-02T14:20:00Z — jira — comment — Confirm response format is {message: 'hello world'}. (Product Owner)
- 2025-01-02T16:00:00Z — jira — status_change — Status change: In Progress -> In Review
- 2025-01-02T17:30:00Z — confluence — page — Hello World Service Spec (v3)
- 2025-01-03T11:40:00Z — jira — comment — Updated per feedback; added docs (Dev B)
- 2025-01-03T16:00:00Z — jira — status_change — Status change: In Review -> Done

## Activity Summary
- **Comments**: 5 (Dev A: 2, Dev B: 2, Scrum Master: 1, Product Owner: 1)
- **Status Transitions**: 3 (To Do → In Progress → In Review → Done)
- **GitHub PR**: #42 (2 files changed)
- **Confluence Page**: Hello World Service Spec (v3)

## Notes & Follow-ups
- Ensure README documents GET /hello and sample response.
- Add API schema entry for GET /hello with 200 response `{ "message": "hello world" }`.
- Schedule post-release validation checklist.

---

## PR Confidence (Markdown)

# PR Confidence Report (Example)

## Inputs
- **Jira**: HELLO-2 — Create Hello World Service
- **GitHub PR**: owner/repo#42
- **Confluence**: Hello World Service Spec

## Extracted Endpoints
- **From Jira**: /hello
- **From PR (patches)**: /hello
- **From Confluence**: (none)

## File-by-File Suggestions
- app/main.py
  - Suggestion: Review patch: check for style, tests, and endpoint contracts.
- tests/test_hello.py
  - Suggestion: Review patch: check for style, tests, and endpoint contracts.

## Confidence Score
- **Score**: 80
- **Rationale**: PR implements 1/1 Jira endpoints. No extra endpoints. Confluence lacks explicit endpoint mention.

## Summary
PR appears to implement 1 of 1 described endpoints. Extras: 0.

---

## How-To: Jira Staleness (Duplicates + Summary)

List candidates (JSON):

```bash
curl -s "http://localhost:5085/reports/jira/staleness?min_confidence=0.4&min_duplicate_confidence=0.5&limit=20" | jq
```

With summary (uses summarizer-hub):

```bash
curl -s "http://localhost:5085/reports/jira/staleness?summarize=true&min_confidence=0.5&limit=10" | jq
```

Response shape:

```json
{
  "items": [
    {"id": "jira:ENG-101", "confidence": 0.72, "flags": ["stale","redundant_candidate"], "sources": {"confluence": 2, "github": 1}, "duplicates": ["jira:ENG-102"], "duplicate_confidence": 0.83}
  ],
  "summary": "ENG-101 likely obsolete; ENG-102 duplicate."
}
```

## How-To: Duplicate Clusters

List duplicate clusters:

```bash
curl -s "http://localhost:5085/reports/duplicates/clusters?min_confidence=0.6&limit=10" | jq
```

Response shape:

```json
{
  "clusters": [
    {
      "id": "cluster-1",
      "confidence": 0.85,
      "items": [
        {"id": "jira:ENG-101", "type": "jira", "title": "API Documentation"},
        {"id": "confluence:123", "type": "confluence", "title": "API Docs"}
      ],
      "evidence": ["Both mention /api/v1 endpoints", "Similar content structure"]
    }
  ]
}
```

## How-To: Ingestion Jobs

### Analytics Ingestion
```bash
curl -X POST "http://localhost:5085/jobs/ingest-analytics" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

### Jira Activity Ingestion
```bash
curl -X POST "http://localhost:5085/jobs/ingest-jira-activity" \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

### GitHub Release Ingestion
```bash
curl -X POST "http://localhost:5085/jobs/ingest-github-release" \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}'
```

### Confluence Backlinks Ingestion
```bash
curl -X POST "http://localhost:5085/jobs/ingest-confluence-backlinks" \
  -H "Content-Type: application/json" \
  -d '{"limit": 200}'
```

## How-To: Webhooks

### Jira Webhook
```bash
curl -X POST "http://localhost:5085/webhooks/jira" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_key": "ENG-101",
    "watchers": 5,
    "last_updated": "2025-01-15T10:30:00Z"
  }'
```

### Confluence Webhook
```bash
curl -X POST "http://localhost:5085/webhooks/confluence" \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123",
    "views": 150,
    "unique_views": 120
  }'
```

### GitHub Webhook
```bash
curl -X POST "http://localhost:5085/webhooks/github" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "org/repo",
    "traffic_views": 1000,
    "traffic_unique": 800
  }'
```