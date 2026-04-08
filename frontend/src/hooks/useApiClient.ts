"use client";

import { useMemo } from "react";
import { useAuth, useUser } from "@clerk/nextjs";

import { APIClient } from "@/lib/api";

export function useApiClient(): APIClient {
  const { getToken, userId } = useAuth();
  const { user } = useUser();

  return useMemo(() => {
    return new APIClient({
      tokenProvider: async () => {
        const token = await getToken();
        return token ?? null;
      },
      devUserIdProvider: async () => userId ?? null,
      emailProvider: async () => user?.primaryEmailAddress?.emailAddress ?? null,
    });
  }, [getToken, user, userId]);
}
