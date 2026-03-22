import { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";

interface HistoryPanelProps {
  title: string;
  loading: boolean;
  empty: boolean;
  syncing?: boolean;
  children: ReactNode;
  className?: string;
}

export function HistoryPanel({ title, loading, empty, syncing = false, children, className }: HistoryPanelProps) {
  return (
    <section className={cn("rounded-editorial border border-black/[0.03] bg-white/60 backdrop-blur-sm p-6 shadow-soft-glow", className)}>
      <div className="mb-6 flex items-center justify-between gap-2">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-foreground/60">{title}</h2>
        {syncing ? (
          <span className="rounded-full bg-vibrant/5 px-3 py-1 text-[9px] font-bold uppercase tracking-widest text-vibrant border border-vibrant/10">
            Syncing
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
        </div>
      ) : empty ? (
        <p className="text-sm text-foreground/30 font-medium italic">No recent activity detected.</p>
      ) : (
        <div className="space-y-3">{children}</div>
      )}
    </section>
  );
}
