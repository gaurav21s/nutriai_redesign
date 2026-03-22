"use client";

import { createContext, createElement, type ReactNode, useContext, useMemo } from "react";
import { ConvexProvider, ConvexReactClient } from "convex/react";

const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;
const OptionalConvexClientContext = createContext<ConvexReactClient | null>(null);

export function useOptionalConvexClient(): ConvexReactClient | null {
  return useContext(OptionalConvexClientContext);
}

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  const client = useMemo(() => {
    if (!convexUrl) {
      return null;
    }
    return new ConvexReactClient(convexUrl);
  }, []);

  if (!client) {
    return createElement(OptionalConvexClientContext.Provider, { value: null }, children);
  }

  return createElement(
    OptionalConvexClientContext.Provider,
    { value: client },
    createElement(ConvexProvider, { client }, children),
  );
}
