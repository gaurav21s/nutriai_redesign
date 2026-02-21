import { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface HistoryPanelProps {
  title: string;
  loading: boolean;
  empty: boolean;
  syncing?: boolean;
  children: ReactNode;
}

export function HistoryPanel({ title, loading, empty, syncing = false, children }: HistoryPanelProps) {
  return (
    <Card className="border-accent-200/70 bg-white/92">
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-lg">{title}</CardTitle>
          {syncing ? (
            <span className="rounded-full bg-brand-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-700">
              Syncing
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : empty ? (
          <p className="text-sm text-accent-500">No history yet.</p>
        ) : (
          <div className="space-y-3">{children}</div>
        )}
      </CardContent>
    </Card>
  );
}
