"use client";

import { useCallback, useState } from "react";

import { captureException } from "@/lib/posthog";

export function useAsyncAction<TArgs extends unknown[], TResult>(action: (...args: TArgs) => Promise<TResult>) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await action(...args);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unexpected error";
        captureException(err, {
          source: "useAsyncAction",
          action_name: action.name || "anonymous_async_action",
        });
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [action]
  );

  return { execute, loading, error, clearError: () => setError(null) };
}
