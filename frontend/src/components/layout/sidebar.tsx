"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Apple,
  BookOpen,
  Calculator,
  ChartPie,
  ClipboardList,
  FileText,
  House,
  MessageSquare,
  Search,
  Sparkles,
  Soup,
  TrendingUp,
  Users,
} from "lucide-react";

import { cn } from "@/lib/cn";

type NavItem = { href: string; label: string; icon: LucideIcon };
type NavTab = { id: string; label: string; items: NavItem[] };

const navTabs: NavTab[] = [
  {
    id: "workflow",
    label: "Workflow",
    items: [
      { href: "/food-insight", label: "Food Insight", icon: ChartPie },
      { href: "/ingredient-checker", label: "Ingredient Checker", icon: Search },
      { href: "/meal-planner", label: "Meal Planner", icon: ClipboardList },
      { href: "/recipe-finder", label: "Recipe Finder", icon: Soup },
    ],
  },
  {
    id: "coach",
    label: "Coach",
    items: [
      { href: "/nutri-chat", label: "Nutri Chat", icon: MessageSquare },
      { href: "/recommendations", label: "Recommendations", icon: Apple },
      { href: "/nutri-quiz", label: "Nutri Quiz", icon: Sparkles },
      { href: "/nutri-calc", label: "Nutri Calc", icon: Calculator },
    ],
  },
  {
    id: "library",
    label: "Library",
    items: [
      { href: "/", label: "Home", icon: House },
      { href: "/articles", label: "Articles", icon: BookOpen },
      { href: "/docs", label: "Docs", icon: FileText },
      { href: "/about", label: "About", icon: Users },
    ],
  },
];

function findTabForPath(pathname: string): string {
  for (const tab of navTabs) {
    for (const item of tab.items) {
      const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
      if (isActive) return tab.id;
    }
  }
  return "workflow";
}

export function Sidebar() {
  const pathname = usePathname();
  const [activeTab, setActiveTab] = useState<string>(() => findTabForPath(pathname));

  useEffect(() => {
    setActiveTab(findTabForPath(pathname));
  }, [pathname]);

  const tabItems = useMemo(() => navTabs.find((tab) => tab.id === activeTab)?.items ?? navTabs[0].items, [activeTab]);

  return (
    <aside className="xl:sticky xl:top-[5.35rem] xl:h-[calc(100vh-6.6rem)] xl:overflow-y-auto">
      <div className="space-y-5">
        <div className="rounded-3xl border border-accent-200/70 bg-accent-900 px-5 py-6 text-white shadow-card">
          <div className="flex items-center gap-3">
            <Image src="/nutriai-color.png" alt="NutriAI logo" width={56} height={56} className="rounded-2xl" />
            <div>
              <p className="font-display text-2xl leading-none text-brand-200">NutriAI</p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-surface-100/95">Nutrition Companion</p>
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-white/15 bg-white/10 px-3 py-3">
            <p className="inline-flex items-center gap-1 text-xs uppercase tracking-[0.18em] text-brand-100">
              <TrendingUp className="h-3.5 w-3.5" />
              Flow
            </p>
            <p className="mt-1 text-sm text-surface-100/95">Analyze → Plan → Refine → Track</p>
          </div>
        </div>

        <div className="rounded-3xl border border-accent-200/70 bg-white/90 p-4 shadow-card">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-500">Navigation</p>

          <div className="mt-3 grid grid-cols-3 gap-1 rounded-2xl border border-accent-200/70 bg-surface-50 p-1">
            {navTabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "rounded-xl px-2 py-2 text-xs font-semibold tracking-[0.08em] transition",
                  activeTab === tab.id ? "bg-white text-accent-900 shadow-soft" : "text-accent-600 hover:text-accent-800"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <nav className="mt-3 space-y-1.5">
            {tabItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all",
                    isActive
                      ? "border border-brand-300 bg-brand-100 text-accent-900 shadow-soft"
                      : "border border-transparent text-accent-700 hover:border-accent-200 hover:bg-surface-50 hover:text-accent-900"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-secondary-700" : "text-accent-500")} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="rounded-3xl border border-accent-200/70 bg-white/88 p-4 shadow-card">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-500">Quick Start</p>
          <div className="mt-3 space-y-2">
            <Link
              href="/food-insight"
              className="block rounded-xl border border-accent-200 bg-surface-50 px-3 py-2.5 text-sm font-semibold text-accent-800 hover:border-brand-300"
            >
              1. Analyze meal
            </Link>
            <Link
              href="/meal-planner"
              className="block rounded-xl border border-accent-200 bg-surface-50 px-3 py-2.5 text-sm font-semibold text-accent-800 hover:border-brand-300"
            >
              2. Build plan
            </Link>
            <Link
              href="/nutri-chat"
              className="block rounded-xl border border-accent-200 bg-surface-50 px-3 py-2.5 text-sm font-semibold text-accent-800 hover:border-brand-300"
            >
              3. Refine strategy
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
}
