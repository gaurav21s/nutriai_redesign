"use client";

import { ReactNode, useState } from "react";
import { PanelRightClose, PanelRightOpen } from "lucide-react";

import { cn } from "@/lib/cn";

interface FeatureShellProps {
  title: string;
  description: string;
  children: ReactNode;
  aside?: ReactNode;
  className?: string;
}

export function FeatureShell({ title, description, children, aside, className }: FeatureShellProps) {
  const [showAside, setShowAside] = useState(false);

  return (
    <div className={cn("space-y-5", className)}>
      <section className="flex items-start justify-between gap-4 border-b border-black/[0.08] pb-4">
        <div>
          <h1 className="text-3xl font-display text-foreground">{title}</h1>
          <p className="mt-1 max-w-3xl text-sm text-foreground/65">{description}</p>
        </div>

        {aside ? (
          <button
            type="button"
            onClick={() => setShowAside((prev) => !prev)}
            className="inline-flex items-center gap-2 rounded-editorial border border-black/[0.12] bg-white px-3 py-2 text-sm text-foreground hover:bg-muted"
          >
            {showAside ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
            {showAside ? "Hide History" : "Show History"}
          </button>
        ) : null}
      </section>

      <div className={cn("grid gap-5", showAside && aside ? "xl:grid-cols-[minmax(0,1fr)_320px]" : "grid-cols-1")}>
        <section className="app-panel p-6">{children}</section>
        {showAside && aside ? <aside className="xl:h-fit">{aside}</aside> : null}
      </div>
    </div>
  );
}
