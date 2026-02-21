"use client";

import { useMemo } from "react";
import { useAuth } from "@clerk/nextjs";

import { APIClient } from "@/lib/api";

export function useApiClient(): APIClient {
  const { getToken, userId } = useAuth();

  return useMemo(() => {
    return new APIClient({
      tokenProvider: async () => {
        const token = await getToken();
        return token ?? null;
      },
      devUserIdProvider: async () => userId ?? null,
    });
  }, [getToken, userId]);
}
