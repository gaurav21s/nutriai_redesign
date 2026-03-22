"use client";

import { ClerkProvider } from "@clerk/nextjs";
import type { ReactNode } from "react";

import { PostHogProvider } from "@/components/providers/posthog-provider";
import { ConvexClientProvider } from "@/lib/convex";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <ConvexClientProvider>
        <PostHogProvider>{children}</PostHogProvider>
      </ConvexClientProvider>
    </ClerkProvider>
  );
}
