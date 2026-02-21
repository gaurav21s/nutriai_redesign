"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useConvex } from "convex/react";

interface UseConvexHistoryOptions {
  functionName: string;
  clerkUserId: string | null | undefined;
  limit?: number;
  pollIntervalMs?: number;
}

interface RefreshOptions {
  attempts?: number;
  intervalMs?: number;
}

export function useConvexHistory<T>({
  functionName,
  clerkUserId,
  limit = 20,
  pollIntervalMs,
}: UseConvexHistoryOptions) {
  const convex = useConvex();
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const refreshTimers = useRef<number[]>([]);

  const clearRefreshTimers = useCallback(() => {
    refreshTimers.current.forEach((timer) => window.clearTimeout(timer));
    refreshTimers.current = [];
  }, []);

  const load = useCallback(
    async (options: { silent?: boolean } = {}) => {
      const { silent = false } = options;

      if (!clerkUserId) {
        setData([]);
        if (!silent) {
          setLoading(false);
          setError(null);
        }
        return;
      }

      if (!silent) {
        setLoading(true);
        setError(null);
      }

      try {
        const result = (await (convex as any).query(functionName as any, {
          clerk_user_id: clerkUserId,
          limit,
        })) as T[];
        setData(result ?? []);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unable to load Convex history";
        setError(message);
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [clerkUserId, convex, functionName, limit]
  );

  const refreshInBackground = useCallback(
    ({ attempts = 4, intervalMs = 1200 }: RefreshOptions = {}) => {
      clearRefreshTimers();
      void load({ silent: true });

      for (let index = 1; index < attempts; index += 1) {
        const timer = window.setTimeout(() => {
          void load({ silent: true });
        }, index * intervalMs);
        refreshTimers.current.push(timer);
      }
    },
    [clearRefreshTimers, load]
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!pollIntervalMs || !clerkUserId) return;

    const timer = window.setInterval(() => {
      void load({ silent: true });
    }, pollIntervalMs);

    return () => window.clearInterval(timer);
  }, [clerkUserId, load, pollIntervalMs]);

  useEffect(() => clearRefreshTimers, [clearRefreshTimers]);

  return {
    data,
    loading,
    error,
    refetch: () => load(),
    refreshInBackground,
  };
}
