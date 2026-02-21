import Link from "next/link";
import { ReactNode } from "react";
import { ArrowRight, CalendarClock, FlaskConical, Sparkles } from "lucide-react";

import { Sidebar } from "@/components/layout/sidebar";
import { WorkspaceTabs } from "@/components/layout/workspace-tabs";

const flowItems = [
  { label: "Analyze", href: "/food-insight" },
  { label: "Plan", href: "/meal-planner" },
  { label: "Cook", href: "/recipe-finder" },
  { label: "Track", href: "/nutri-calc" },
];

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[calc(100vh-4rem)]">
      <div className="mx-auto w-full max-w-[1480px] px-4 py-7 sm:px-6 lg:px-8">
        <div className="grid gap-7 xl:grid-cols-[300px_minmax(0,1fr)]">
          <Sidebar />

          <main className="space-y-7">
            <section className="relative overflow-hidden rounded-[2rem] border border-accent-200/70 bg-white/90 px-6 py-6 shadow-card sm:px-7">
              <div className="pointer-events-none absolute -right-12 -top-12 h-52 w-52 rounded-full bg-brand-100/55 blur-2xl" />
              <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">
                <div>
                  <p className="inline-flex items-center gap-1.5 rounded-full bg-surface-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent-700">
                    <Sparkles className="h-3.5 w-3.5 text-secondary-600" />
                    NutriAI Workspace
                  </p>
                  <h1 className="mt-3 text-3xl font-semibold text-accent-900 sm:text-4xl">
                    Daily Nutrition Dashboard
                  </h1>
                  <p className="mt-2 max-w-2xl text-sm text-accent-700 sm:text-base">
                    Start with analysis. Move to planning. Close the loop with chat and tracking.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    href="/food-insight"
                    className="inline-flex items-center gap-2 rounded-xl border border-brand-300 bg-brand-100 px-3.5 py-2 text-sm font-semibold text-accent-900 transition hover:border-brand-400"
                  >
                    <FlaskConical className="h-4 w-4 text-secondary-700" />
                    Start Analysis
                  </Link>
                  <Link
                    href="/docs"
                    className="inline-flex items-center gap-2 rounded-xl border border-accent-300 bg-surface-50 px-3.5 py-2 text-sm font-semibold text-accent-800 transition hover:border-brand-300 hover:text-accent-900"
                  >
                    <CalendarClock className="h-4 w-4 text-secondary-700" />
                    Docs
                  </Link>
                </div>
              </div>

              <div className="mt-5 grid gap-2 sm:grid-cols-4">
                {flowItems.map((item, index) => (
                  <Link
                    key={item.label}
                    href={item.href}
                    className="group rounded-xl border border-accent-200/80 bg-surface-50 px-3 py-2.5 text-sm transition hover:border-brand-300 hover:bg-brand-50"
                  >
                    <p className="text-[11px] uppercase tracking-[0.14em] text-accent-500">Step {index + 1}</p>
                    <p className="mt-0.5 inline-flex items-center gap-1.5 font-semibold text-accent-800 group-hover:text-accent-900">
                      {item.label}
                      <ArrowRight className="h-3.5 w-3.5 text-accent-500 group-hover:text-secondary-700" />
                    </p>
                  </Link>
                ))}
              </div>
            </section>

            <WorkspaceTabs />

            <div className="animate-fade-up">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
