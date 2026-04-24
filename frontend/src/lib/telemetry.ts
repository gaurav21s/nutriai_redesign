"use client";

export interface FrontendTelemetryIdentity {
  clerk_user_id?: string | null;
  email?: string | null;
}

export interface FrontendTelemetryEventInput {
  event_type: string;
  category?: string;
  feature?: string;
  status?: string;
  request_id?: string;
  backend_request_id?: string | null;
  path?: string;
  route?: string;
  properties?: Record<string, unknown>;
}

const TELEMETRY_ENDPOINT = "/api/telemetry/events";
const SESSION_STORAGE_KEY = "nutriai.telemetry.session_id";

let inMemorySessionId: string | null = null;

function createId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getBrowserSessionId(): string {
  if (typeof window === "undefined") {
    return "server-render";
  }

  if (inMemorySessionId) {
    return inMemorySessionId;
  }

  try {
    const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (existing) {
      inMemorySessionId = existing;
      return existing;
    }
  } catch {
    // Ignore storage access failures and fall back to in-memory session state.
  }

  const nextId = createId();
  inMemorySessionId = nextId;

  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, nextId);
  } catch {
    // Ignore storage access failures and keep the in-memory session id.
  }

  return nextId;
}

export function createRequestCorrelation(): {
  requestId: string;
  clientEventId: string;
  clientSessionId: string;
  clientRoute: string;
} {
  return {
    requestId: createId(),
    clientEventId: createId(),
    clientSessionId: getBrowserSessionId(),
    clientRoute: getCurrentRoute(),
  };
}

export function getCurrentRoute(): string {
  if (typeof window === "undefined") {
    return "server";
  }

  const pathname = window.location.pathname || "/";
  const search = window.location.search || "";
  return `${pathname}${search}`;
}

export function buildClientCorrelationHeaders(
  correlation: ReturnType<typeof createRequestCorrelation>,
  identity?: FrontendTelemetryIdentity,
): Record<string, string> {
  return {
    "x-request-id": correlation.requestId,
    "x-client-session-id": correlation.clientSessionId,
    "x-client-event-id": correlation.clientEventId,
    "x-client-route": correlation.clientRoute,
    ...(identity?.email ? { "x-user-email": identity.email } : {}),
  };
}

export async function emitFrontendTelemetry(
  event: FrontendTelemetryEventInput,
  identity?: FrontendTelemetryIdentity,
): Promise<void> {
  if (typeof window === "undefined") {
    return;
  }

  const payload = {
    events: [
      {
        client_event_id: createId(),
        client_session_id: getBrowserSessionId(),
        route: getCurrentRoute(),
        clerk_user_id: identity?.clerk_user_id ?? undefined,
        user_email: identity?.email ?? undefined,
        ...event,
      },
    ],
  };

  try {
    await fetch(TELEMETRY_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      credentials: "same-origin",
      keepalive: true,
    });
  } catch {
    // Telemetry failures should never interrupt the product flow.
  }
}
