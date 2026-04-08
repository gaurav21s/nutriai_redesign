"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { PostHogErrorBoundary, PostHogProvider as PostHogReactProvider } from "posthog-js/react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useRef } from "react";
import { usePathname } from "next/navigation";

import { APIClient } from "@/lib/api";
import { useOptionalConvexClient } from "@/lib/convex";
import { initPostHog, isPostHogEnabled, posthog, resolveConvexDeploymentKey } from "@/lib/posthog";
import { emitFrontendTelemetry } from "@/lib/telemetry";

interface ConvexUserRecord {
  id: string;
  clerk_user_id: string;
  email?: string;
  name?: string;
  image_url?: string;
  permissions?: Record<string, boolean>;
  is_demo?: boolean;
  tier?: string;
  created_at?: string;
}

export function PostHogProvider({ children }: { children: ReactNode }) {
  const { getToken, userId } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  const convex = useOptionalConvexClient();
  const pathname = usePathname();
  const syncedIdentityRef = useRef<string | null>(null);
  const convexDeploymentKey = resolveConvexDeploymentKey();

  const api = useMemo(() => {
    return new APIClient({
      tokenProvider: async () => {
        const token = await getToken();
        return token ?? null;
      },
      devUserIdProvider: async () => userId ?? null,
      emailProvider: async () => user?.primaryEmailAddress?.emailAddress ?? null,
    });
  }, [getToken, user, userId]);

  useEffect(() => {
    initPostHog();
  }, []);

  useEffect(() => {
    void emitFrontendTelemetry(
      {
        event_type: "frontend_route_view",
        category: "navigation",
        feature: "page_view",
        status: "completed",
        path: pathname,
        properties: {
          pathname,
        },
      },
      {
        clerk_user_id: userId ?? undefined,
        email: user?.primaryEmailAddress?.emailAddress ?? undefined,
      }
    );
  }, [pathname, user, userId]);

  useEffect(() => {
    function handleError(event: ErrorEvent) {
      void emitFrontendTelemetry(
        {
          event_type: "frontend_window_error",
          category: "error",
          feature: "window",
          status: "failed",
          properties: {
            message: event.message,
            source: event.filename,
            line: event.lineno,
            column: event.colno,
          },
        },
        {
          clerk_user_id: userId ?? undefined,
          email: user?.primaryEmailAddress?.emailAddress ?? undefined,
        }
      );
    }

    function handleUnhandledRejection(event: PromiseRejectionEvent) {
      const reason = event.reason instanceof Error ? event.reason.message : String(event.reason ?? "unknown");
      void emitFrontendTelemetry(
        {
          event_type: "frontend_unhandled_rejection",
          category: "error",
          feature: "promise",
          status: "failed",
          properties: {
            reason,
          },
        },
        {
          clerk_user_id: userId ?? undefined,
          email: user?.primaryEmailAddress?.emailAddress ?? undefined,
        }
      );
    }

    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleUnhandledRejection);

    return () => {
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleUnhandledRejection);
    };
  }, [user, userId]);

  useEffect(() => {
    if (!isPostHogEnabled() || !isLoaded) {
      return;
    }

    if (!isSignedIn || !user) {
      if (syncedIdentityRef.current !== null) {
        posthog.reset();
        syncedIdentityRef.current = null;
      }
      return;
    }

    const currentUser = user;
    let cancelled = false;

    async function syncIdentity() {
      const [subscriptionResult, convexUserResult] = await Promise.allSettled([
        api.getCurrentSubscription(),
        convex
          ? ((convex as any).query("users:getByClerkUserId" as any, {
              clerk_user_id: currentUser.id,
            }) as Promise<ConvexUserRecord | null>)
          : Promise.resolve(null),
      ]);

      if (cancelled) {
        return;
      }

      const subscription =
        subscriptionResult.status === "fulfilled" ? subscriptionResult.value.subscription : null;
      const convexUser = convexUserResult.status === "fulfilled" ? convexUserResult.value : null;

      const personProperties: Record<string, unknown> = {
        auth_provider: "clerk",
        clerk_user_id: currentUser.id,
        email: currentUser.primaryEmailAddress?.emailAddress ?? convexUser?.email,
        name: currentUser.fullName ?? convexUser?.name,
        username: currentUser.username ?? undefined,
        avatar_url: currentUser.imageUrl ?? convexUser?.image_url,
        subscription_tier: subscription?.tier,
        subscription_status: subscription?.status,
        subscription_currency: subscription?.currency,
        subscription_amount: subscription?.amount,
        is_demo_user: subscription?.is_demo ?? convexUser?.is_demo ?? false,
        convex_user_id: convexUser?.id,
        convex_user_synced: Boolean(convexUser),
        convex_user_tier: convexUser?.tier,
        convex_permissions_count: Object.keys(convexUser?.permissions ?? {}).length,
        convex_deployment: convexDeploymentKey,
      };

      const syncSignature = JSON.stringify(personProperties);
      if (syncedIdentityRef.current === syncSignature) {
        return;
      }

      posthog.identify(currentUser.id, personProperties);
      posthog.setPersonPropertiesForFlags(personProperties, true);
      posthog.register({
        auth_provider: "clerk",
        clerk_user_id: currentUser.id,
        subscription_tier: subscription?.tier ?? "unknown",
        subscription_status: subscription?.status ?? "unknown",
        convex_user_id: convexUser?.id ?? "none",
        convex_deployment: convexDeploymentKey ?? "unknown",
      });

      if (subscription) {
        posthog.group("subscription_tier", subscription.tier, {
          label: subscription.tier.toUpperCase(),
          status: subscription.status,
          currency: subscription.currency,
          is_demo: subscription.is_demo,
        });
      }

      if (convexDeploymentKey) {
        posthog.group("convex_deployment", convexDeploymentKey, {
          convex_url: process.env.NEXT_PUBLIC_CONVEX_URL,
        });
      }

      syncedIdentityRef.current = syncSignature;
    }

    void syncIdentity();

    return () => {
      cancelled = true;
    };
  }, [api, convex, convexDeploymentKey, isLoaded, isSignedIn, pathname, user]);

  if (!isPostHogEnabled()) {
    return children;
  }

  return (
    <PostHogReactProvider client={posthog}>
      <PostHogErrorBoundary>{children}</PostHogErrorBoundary>
    </PostHogReactProvider>
  );
}
