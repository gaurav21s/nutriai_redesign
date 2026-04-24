# Axiom Observability Runbook

NutriAI now emits:

- Backend wide request events to `nutriai-backend-logs`
- Frontend browser events to `nutriai-frontend-events`
- OpenTelemetry traces to `nutriai-traces`

## Required Environment Variables

Set these anywhere the backend and frontend actually run:

```bash
AXIOM_API_TOKEN=...
AXIOM_DOMAIN=https://us-east-1.aws.edge.axiom.co
AXIOM_BACKEND_LOGS_DATASET=nutriai-backend-logs
AXIOM_FRONTEND_EVENTS_DATASET=nutriai-frontend-events
AXIOM_TRACES_DATASET=nutriai-traces
OTEL_SERVICE_NAMESPACE=nutriai
OTEL_TRACE_SAMPLE_RATE=1.0
LOG_SLOW_REQUEST_MS=1500
LOG_SUCCESS_SAMPLE_RATE=1.0
LOG_VIP_USER_IDS=
```

Notes:

- The backend exports logs and traces only when `AXIOM_API_TOKEN` is present.
- The frontend never exposes the token in the browser. It posts sanitized events to `POST /api/telemetry/events`, and that Next.js route forwards them to Axiom server-side.
- Rotate any previously shared token before production use.

## Important Fields

These are the main join keys across datasets:

- `clerk_user_id`
- `user_email`
- `client_session_id`
- `client_event_id`
- `request_id`
- `trace_id`
- `span_id`

Helpful backend fields:

- `feature`
- `path`
- `route`
- `method`
- `status_code`
- `latency_ms`
- `error_code`
- `outcome`

Helpful frontend fields:

- `event_type`
- `category`
- `feature`
- `route`
- `backend_request_id`

## APL Queries

Trace one user through frontend events:

```apl
['nutriai-frontend-events']
| where clerk_user_id == 'user_123'
| sort by timestamp desc
| project timestamp, event_type, feature, route, request_id, backend_request_id, client_session_id, status
| limit 200
```

Trace one user through backend request summaries:

```apl
['nutriai-backend-logs']
| where clerk_user_id == 'user_123' and event_type == 'request_summary'
| sort by timestamp desc
| project timestamp, feature, method, path, status_code, latency_ms, request_id, trace_id, error_code, outcome
| limit 200
```

Follow one browser session across both datasets:

```apl
['nutriai-frontend-events']
| where client_session_id == 'session_123'
| project timestamp, source='frontend', event_type, feature, route, request_id, backend_request_id
| union (
    ['nutriai-backend-logs']
    | where client_session_id == 'session_123' and event_type == 'request_summary'
    | project timestamp, source='backend', event_type, feature, route=path, request_id, backend_request_id=request_id
  )
| sort by timestamp desc
| limit 300
```

Find slow requests worth investigating:

```apl
['nutriai-backend-logs']
| where event_type == 'request_summary' and latency_ms >= 1500
| sort by latency_ms desc
| project timestamp, clerk_user_id, feature, method, path, status_code, latency_ms, request_id, trace_id
| limit 100
```

Find error-heavy users:

```apl
['nutriai-backend-logs']
| where event_type == 'request_summary' and status_code >= 400
| summarize error_count = count() by clerk_user_id, user_email
| sort by error_count desc
| limit 50
```

Start from a support ticket request ID:

```apl
['nutriai-backend-logs']
| where request_id == 'request_123'
| project timestamp, clerk_user_id, user_email, feature, path, status_code, latency_ms, trace_id, error_code, error_message
| limit 20
```

## Local Validation Checklist

- Start the backend and frontend with the Axiom env vars set.
- Sign in and complete one feature flow, for example meal planner or recipe finder.
- Confirm the frontend dataset receives `frontend_route_view` and `frontend_api_request_completed` events.
- Confirm the backend dataset receives one `request_summary` event per API request.
- Pick one `request_id` and verify the same value appears in the browser event and the backend summary.
- Pick one `trace_id` from the backend logs and verify it exists in `nutriai-traces`.
