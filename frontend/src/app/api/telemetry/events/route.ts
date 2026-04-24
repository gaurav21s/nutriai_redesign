import { NextRequest, NextResponse } from "next/server";

const MAX_EVENTS_PER_REQUEST = 20;
const MAX_DEPTH = 4;
const MAX_STRING_LENGTH = 512;
const REDACTED_KEYS = ["authorization", "cookie", "token", "password", "secret", "api_key", "apikey"];

function getAxiomBaseUrl(): string {
  return (process.env.AXIOM_DOMAIN ?? "https://us-east-1.aws.edge.axiom.co").replace(/\/$/, "");
}

function getAxiomIngestUrl(dataset: string): string {
  const baseUrl = getAxiomBaseUrl();

  if (baseUrl === "https://api.axiom.co") {
    return `${baseUrl}/v1/datasets/${dataset}/ingest`;
  }

  return `${baseUrl}/v1/ingest/${dataset}`;
}

function sanitizeValue(value: unknown, depth = 0): unknown {
  if (depth > MAX_DEPTH) {
    return "[truncated]";
  }

  if (value === null || typeof value === "number" || typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value.length > MAX_STRING_LENGTH ? `${value.slice(0, MAX_STRING_LENGTH)}...[truncated]` : value;
  }

  if (Array.isArray(value)) {
    return value.slice(0, 50).map((item) => sanitizeValue(item, depth + 1));
  }

  if (typeof value === "object") {
    const input = value as Record<string, unknown>;
    const output: Record<string, unknown> = {};

    for (const [key, item] of Object.entries(input)) {
      const lowered = key.toLowerCase();
      if (REDACTED_KEYS.some((fragment) => lowered.includes(fragment))) {
        output[key] = "[redacted]";
        continue;
      }
      output[key] = sanitizeValue(item, depth + 1);
    }

    return output;
  }

  return String(value);
}

export async function POST(request: NextRequest) {
  let payload: unknown;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON payload" }, { status: 400 });
  }

  const events = Array.isArray((payload as { events?: unknown[] })?.events)
    ? ((payload as { events: unknown[] }).events ?? [])
    : [];

  if (events.length === 0) {
    return NextResponse.json({ error: "At least one event is required" }, { status: 400 });
  }

  const dataset = process.env.AXIOM_FRONTEND_EVENTS_DATASET ?? "nutriai-frontend-events";
  const token = process.env.AXIOM_API_TOKEN;

  const sanitizedEvents = events.slice(0, MAX_EVENTS_PER_REQUEST).map((event) => {
    const sanitized = sanitizeValue(event) as Record<string, unknown>;

    return {
      timestamp: new Date().toISOString(),
      source: "frontend",
      environment: process.env.NODE_ENV ?? "development",
      ...sanitized,
    };
  });

  const compactSummary = sanitizedEvents.map((event) => {
    const eventRecord = event as Record<string, unknown>;
    const properties = eventRecord.properties as Record<string, unknown> | undefined;

    return {
      event_type: typeof eventRecord.event_type === "string" ? eventRecord.event_type : undefined,
      category: typeof eventRecord.category === "string" ? eventRecord.category : undefined,
      feature: typeof eventRecord.feature === "string" ? eventRecord.feature : undefined,
      status: typeof eventRecord.status === "string" ? eventRecord.status : undefined,
      route: typeof eventRecord.route === "string" ? eventRecord.route : undefined,
      session_id: typeof properties?.session_id === "string" ? properties.session_id : undefined,
    };
  });

  console.info("[Frontend telemetry] received", {
    events: compactSummary,
    count: compactSummary.length,
  });

  const ingestUrl = getAxiomIngestUrl(dataset);
  if (!token) {
    console.info("[Frontend telemetry] Axiom disabled; events kept in frontend.log only", {
      events: compactSummary,
      count: compactSummary.length,
    });
    return NextResponse.json({ accepted: true, disabled: true }, { status: 202 });
  }

  const response = await fetch(ingestUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(sanitizedEvents),
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    console.error("[Axiom relay] frontend telemetry ingest failed", {
      dataset,
      ingestUrl,
      status: response.status,
      body: body.slice(0, MAX_STRING_LENGTH),
    });
    return NextResponse.json(
      {
        accepted: false,
        status: response.status,
        body: body.slice(0, MAX_STRING_LENGTH),
      },
      { status: 502 },
    );
  }

  console.info("[Axiom relay] frontend telemetry ingested", {
    dataset,
    ingestUrl,
    events: sanitizedEvents.length,
    summaries: compactSummary,
  });
  return NextResponse.json({ accepted: true }, { status: 202 });
}
