"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/cn";

type TabRoute = { label: string; href: string };
type TabGroup = { id: string; label: string; routes: TabRoute[] };

const tabGroups: TabGroup[] = [
  {
    id: "analyze",
    label: "Analyze",
    routes: [
      { label: "Food Insight", href: "/food-insight" },
      { label: "Ingredient Checker", href: "/ingredient-checker" },
    ],
  },
  {
    id: "plan",
    label: "Plan",
    routes: [
      { label: "Meal Planner", href: "/meal-planner" },
      { label: "Recipe Finder", href: "/recipe-finder" },
    ],
  },
  {
    id: "coach",
    label: "Coach",
    routes: [
      { label: "Nutri Chat", href: "/nutri-chat" },
      { label: "Recommendations", href: "/recommendations" },
    ],
  },
  {
    id: "track",
    label: "Track",
    routes: [
      { label: "Nutri Quiz", href: "/nutri-quiz" },
      { label: "Nutri Calc", href: "/nutri-calc" },
    ],
  },
];

function getActiveGroupId(pathname: string): string {
  for (const group of tabGroups) {
    for (const route of group.routes) {
      if (pathname === route.href || pathname.startsWith(route.href)) {
        return group.id;
      }
    }
  }
  return "analyze";
}

export function WorkspaceTabs() {
  const pathname = usePathname();
  const [activeGroupId, setActiveGroupId] = useState<string>(() => getActiveGroupId(pathname));

  useEffect(() => {
    setActiveGroupId(getActiveGroupId(pathname));
  }, [pathname]);

  const activeGroup = useMemo(
    () => tabGroups.find((group) => group.id === activeGroupId) ?? tabGroups[0],
    [activeGroupId]
  );

  return (
    <section className="rounded-2xl border border-accent-200/70 bg-white/86 p-3 shadow-card">
      <div className="grid grid-cols-4 gap-1 rounded-xl border border-accent-200/70 bg-surface-50 p-1">
        {tabGroups.map((group) => (
          <button
            key={group.id}
            type="button"
            onClick={() => setActiveGroupId(group.id)}
            className={cn(
              "rounded-lg px-2 py-2 text-xs font-semibold tracking-[0.08em] transition",
              activeGroupId === group.id ? "bg-white text-accent-900 shadow-soft" : "text-accent-600 hover:text-accent-800"
            )}
          >
            {group.label}
          </button>
        ))}
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        {activeGroup.routes.map((route) => {
          const active = pathname === route.href || pathname.startsWith(route.href);
          return (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-sm font-semibold transition",
                active
                  ? "border-brand-300 bg-brand-100 text-accent-900"
                  : "border-accent-200 bg-white text-accent-700 hover:border-brand-300 hover:text-accent-900"
              )}
            >
              {route.label}
            </Link>
          );
        })}
      </div>
    </section>
  );
}
