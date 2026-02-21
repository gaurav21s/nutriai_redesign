"use client";

import { createElement, type ReactNode, useMemo } from "react";
import { ConvexProvider, ConvexReactClient } from "convex/react";

const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  const client = useMemo(() => {
    if (!convexUrl) {
      throw new Error("NEXT_PUBLIC_CONVEX_URL is not configured");
    }
    return new ConvexReactClient(convexUrl);
  }, []);

  return createElement(ConvexProvider, { client }, children);
}
