"use client";

import posthog from "posthog-js";
import type { CapturedNetworkRequest } from "@posthog/types";

const posthogToken = process.env.NEXT_PUBLIC_POSTHOG_TOKEN ?? process.env.NEXT_PUBLIC_POSTHOG_KEY;
const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";

let posthogInitialized = false;

export function isPostHogEnabled(): boolean {
  return typeof window !== "undefined" && Boolean(posthogToken);
}

export function resolveConvexDeploymentKey(): string | null {
  const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

  if (!convexUrl) {
    return null;
  }

  try {
    return new URL(convexUrl).host;
  } catch {
    return convexUrl;
  }
}

function sanitizeCapturedNetworkRequest(request: CapturedNetworkRequest): CapturedNetworkRequest | null {
  const name = request.name || "";

  return {
    ...request,
    name,
    requestHeaders: undefined,
    requestBody: name.includes("/api/v1/") || name.includes("clerk") ? undefined : request.requestBody,
    responseHeaders: undefined,
    responseBody: undefined,
  };
}

export function initPostHog(): typeof posthog {
  if (posthogInitialized || !posthogToken || typeof window === "undefined") {
    if (!posthogInitialized && typeof window !== "undefined" && !posthogToken && process.env.NODE_ENV !== "production") {
      console.warn(
        "[PostHog] Missing NEXT_PUBLIC_POSTHOG_TOKEN or NEXT_PUBLIC_POSTHOG_KEY; frontend analytics is disabled."
      );
    }
    return posthog;
  }

  posthog.init(posthogToken, {
    api_host: posthogHost,
    autocapture: true,
    capture_pageview: "history_change",
    capture_pageleave: "if_capture_pageview",
    capture_performance: true,
    defaults: "2026-01-30",
    person_profiles: "identified_only",
    mask_personal_data_properties: true,
    session_recording: {
      maskAllInputs: true,
      maskInputOptions: {
        color: false,
        date: true,
        "datetime-local": true,
        email: true,
        month: true,
        number: false,
        password: true,
        range: false,
        search: true,
        select: false,
        tel: true,
        text: true,
        textarea: true,
        time: true,
        url: true,
        week: true,
      },
      recordHeaders: false,
      recordBody: false,
      maskCapturedNetworkRequestFn: sanitizeCapturedNetworkRequest,
    },
    error_tracking: {
      captureExtensionExceptions: false,
    },
  });

  posthogInitialized = true;
  return posthog;
}

export function captureEvent(event: string, properties?: Record<string, unknown>): void {
  if (!isPostHogEnabled()) {
    return;
  }

  initPostHog();
  posthog.capture(event, properties);
}

export function captureException(error: unknown, properties?: Record<string, unknown>): void {
  if (!isPostHogEnabled()) {
    return;
  }

  initPostHog();

  if (error instanceof Error) {
    posthog.captureException(error, properties);
    return;
  }

  posthog.captureException(new Error(typeof error === "string" ? error : "Unexpected client error"), properties);
}

export { posthog };
