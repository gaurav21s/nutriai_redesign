"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
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

const workspaceLinks = [
  { href: "/food-insight", label: "Food Insight", icon: ChartPie },
  { href: "/ingredient-checker", label: "Ingredient Checker", icon: Search },
  { href: "/meal-planner", label: "Meal Planner", icon: ClipboardList },
  { href: "/recipe-finder", label: "Recipe Finder", icon: Soup },
];

const trackingLinks = [
  { href: "/nutri-quiz", label: "Nutri Quiz", icon: Sparkles },
  { href: "/nutri-calc", label: "Nutri Calc", icon: Calculator },
  { href: "/nutri-chat", label: "Nutri Chat", icon: MessageSquare },
  { href: "/recommendations", label: "Recommendations", icon: Apple },
];

const knowledgeLinks = [
  { href: "/", label: "Home", icon: House },
  { href: "/articles", label: "Articles", icon: BookOpen },
  { href: "/docs", label: "Docs", icon: FileText },
  { href: "/about", label: "About", icon: Users },
];

function NavGroup({
  title,
  items,
  pathname,
}: {
  title: string;
  items: Array<{ href: string; label: string; icon: LucideIcon }>;
  pathname: string;
}) {
  return (
    <section className="space-y-2.5">
      <p className="px-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent-500">{title}</p>
      <nav className="space-y-1.5">
        {items.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all",
                active
                  ? "border border-brand-300 bg-brand-100 text-accent-900 shadow-soft"
                  : "border border-transparent text-accent-700 hover:border-accent-200 hover:bg-surface-50 hover:text-accent-900"
              )}
            >
              <Icon className={cn("h-4 w-4", active ? "text-secondary-700" : "text-accent-500")} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </section>
  );
}

export function Sidebar() {
  const pathname = usePathname();

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
            <p className="mt-1 text-sm text-surface-100/95">Analyze → Plan → Track</p>
          </div>
        </div>

        <div className="space-y-4 rounded-3xl border border-accent-200/70 bg-white/88 p-4 shadow-card">
          <NavGroup title="Analyze + Build" items={workspaceLinks} pathname={pathname} />
          <div className="h-px bg-accent-200/70" />
          <NavGroup title="Track + Improve" items={trackingLinks} pathname={pathname} />
          <div className="h-px bg-accent-200/70" />
          <NavGroup title="Library" items={knowledgeLinks} pathname={pathname} />
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
              2. Generate plan
            </Link>
            <Link
              href="/nutri-chat"
              className="block rounded-xl border border-accent-200 bg-surface-50 px-3 py-2.5 text-sm font-semibold text-accent-800 hover:border-brand-300"
            >
              3. Refine with chat
            </Link>
          </div>
        </div>
      </div>
    </aside>
  );
}
