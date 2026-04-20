"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { useEffect, useMemo, useState, type ComponentType } from "react";
import {
  Apple,
  ArrowRight,
  Brain,
  Calculator,
  Leaf,
  MessageSquare,
  Microscope,
  Settings,
  ShieldCheck,
  Sparkles,
  Soup,
} from "lucide-react";

import { useConvexHistory } from "@/hooks/useConvexHistory";

/* ── data ─────────────────────────────────────────────── */

type Tool = {
  title: string;
  description: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
};

const groups: { label: string; items: Tool[] }[] = [
  {
    label: "Analyze",
    items: [
      { title: "Food Insight", description: "Analyze meals from text or image.", href: "/food-insight", icon: Brain },
      { title: "Ingredient Checker", description: "Check ingredient safety.", href: "/ingredient-checker", icon: Microscope },
      { title: "Nutri Quiz", description: "Test your nutrition knowledge.", href: "/nutri-quiz", icon: Sparkles },
    ],
  },
  {
    label: "Plan",
    items: [
      { title: "Meal Planner", description: "Generate a daily meal plan.", href: "/meal-planner", icon: Leaf },
      { title: "Recipe Finder", description: "Get recipes and shopping links.", href: "/recipe-finder", icon: Soup },
    ],
  },
  {
    label: "Refine",
    items: [
      { title: "Nutri Smart Picks", description: "Rank the best real-world choice for your goal.", href: "/nutri-smart-picks", icon: Apple },
      { title: "Nutri Chat", description: "Ask anything, get quick help.", href: "/nutri-chat", icon: MessageSquare },
    ],
  },
  {
    label: "Track",
    items: [
      { title: "Nutri Calc", description: "Track BMI and daily calories.", href: "/nutri-calc", icon: Calculator },
      { title: "Library", description: "History and saved items.", href: "/library", icon: Settings },
      { title: "Subscription", description: "Manage plan and access.", href: "/subscription", icon: ShieldCheck },
    ],
  },
];

const activitySources = [
  { label: "Meal plans", functionName: "mealPlans:listByUser", href: "/meal-planner" },
  { label: "Food checks", functionName: "foodInsights:listByUser", href: "/food-insight" },
  { label: "Recipes", functionName: "recipes:listByUser", href: "/recipe-finder" },
  { label: "Agent chats", functionName: "chat:listSessions", href: "/nutri-chat" },
] as const;

type HistoryItem = {
  id?: string;
  created_at?: string;
};

/* ── helpers ──────────────────────────────────────────── */

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function formatCount(count: number): string {
  if (count >= 50) return "50+";
  return String(count);
}

/* ── page ─────────────────────────────────────────────── */

export default function DashboardOverview() {
  const { user } = useUser();
  const name = user?.firstName?.trim();
  const [greet, setGreet] = useState("Welcome back");

  useEffect(() => setGreet(getGreeting()), []);

  const mealPlans = useConvexHistory<HistoryItem>({
    functionName: "mealPlans:listByUser",
    clerkUserId: user?.id,
    limit: 50,
  });
  const foodInsights = useConvexHistory<HistoryItem>({
    functionName: "foodInsights:listByUser",
    clerkUserId: user?.id,
    limit: 50,
  });
  const recipes = useConvexHistory<HistoryItem>({
    functionName: "recipes:listByUser",
    clerkUserId: user?.id,
    limit: 50,
  });
  const chatSessions = useConvexHistory<HistoryItem>({
    functionName: "chat:listSessions",
    clerkUserId: user?.id,
    limit: 50,
  });

  const activity = useMemo(
    () =>
      activitySources.map((source, index) => {
        const histories = [mealPlans.data, foodInsights.data, recipes.data, chatSessions.data];
        return {
          ...source,
          count: histories[index]?.length ?? 0,
        };
      }),
    [chatSessions.data, foodInsights.data, mealPlans.data, recipes.data]
  );

  const totalActivity = activity.reduce((sum, item) => sum + item.count, 0);
  const strongest = activity.reduce((best, item) => (item.count > best.count ? item : best), activity[0]);
  const hasActivity = totalActivity > 0;
  const chartMax = Math.max(1, ...activity.map((item) => item.count));
  const loadingActivity = mealPlans.loading || foodInsights.loading || recipes.loading || chatSessions.loading;

  return (
    <div className="mx-auto w-full max-w-[1080px] pb-14">
      {/* ── hero ── */}
      <div className="animate-fade-up">
        <h1 className="text-3xl leading-tight text-foreground sm:text-[2.25rem]">
          {greet}
          {name ? `, ${name}` : ""}
          <span className="text-vibrant">.</span>
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-foreground/65">
          Pick up where you left off, or start something new.
        </p>
      </div>

      {/* ── chat spotlight ── */}
      <div className="animate-fade-up mt-8" style={{ animationDelay: "80ms" }}>
        <Link
          href="/nutri-chat"
          className="group flex items-center gap-3.5 rounded-editorial border border-vibrant/15 bg-white px-5 py-3.5 transition-colors hover:border-vibrant/30 hover:bg-brand-50/55"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-vibrant text-white">
            <MessageSquare className="h-3.5 w-3.5" />
          </span>
          <span className="flex-1 text-sm text-foreground/65 select-none">
            Ask the Nutri agent about ingredients, meals, or today&apos;s next healthy choice.
          </span>
          <ArrowRight className="h-4 w-4 text-foreground/15 transition-colors group-hover:text-vibrant" />
        </Link>
      </div>

      {/* ── progress snapshot ── */}
      <section className="animate-fade-up mt-8 rounded-editorial border border-black/[0.08] bg-white p-5 sm:p-6" style={{ animationDelay: "120ms" }}>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
          <div>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-xl font-display text-foreground">Your health journey</h2>
                <p className="mt-1 text-sm leading-relaxed text-foreground/65">
                  {loadingActivity
                    ? "Loading your recent activity..."
                    : hasActivity
                      ? `You have completed ${formatCount(totalActivity)} nutrition actions. ${strongest.count ? `${strongest.label} are leading your progress.` : ""}`
                      : "Start with one small action today. A meal plan, food check, or question is enough to build momentum."}
                </p>
              </div>
              <Link
                href="/nutri-calc"
                className="inline-flex items-center gap-2 rounded-editorial border border-black/[0.10] bg-background px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-vibrant/30 hover:text-vibrant"
              >
                Record today&apos;s metric
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="mt-6 space-y-4">
              {activity.map((item) => (
                <Link key={item.label} href={item.href} className="group grid gap-2 sm:grid-cols-[112px_minmax(0,1fr)_44px] sm:items-center">
                  <span className="text-sm font-medium text-foreground/75 transition-colors group-hover:text-foreground">{item.label}</span>
                  <span className="h-2 overflow-hidden rounded-sm bg-black/[0.06]">
                    <span
                      className="block h-full rounded-sm bg-vibrant transition-[width]"
                      style={{ width: `${Math.max(item.count ? 12 : 0, (item.count / chartMax) * 100)}%` }}
                    />
                  </span>
                  <span className="text-left text-sm font-semibold text-foreground sm:text-right">{formatCount(item.count)}</span>
                </Link>
              ))}
            </div>
          </div>

          <div className="border-t border-black/[0.08] pt-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
            <p className="text-sm font-semibold text-foreground">Good next steps</p>
            <div className="mt-3 space-y-3">
              <Link href="/meal-planner" className="group flex items-start gap-3 text-sm leading-relaxed text-foreground/65 hover:text-foreground">
                <Leaf className="mt-0.5 h-4 w-4 flex-shrink-0 text-vibrant" />
                Generate a meal plan for the way you actually eat this week.
              </Link>
              <Link href="/nutri-chat" className="group flex items-start gap-3 text-sm leading-relaxed text-foreground/65 hover:text-foreground">
                <MessageSquare className="mt-0.5 h-4 w-4 flex-shrink-0 text-vibrant" />
                Ask one health question and let the agent use your saved history.
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── tool grid ── */}
      <div className="mt-11 grid gap-x-10 gap-y-10 sm:grid-cols-2">
        {groups.map(({ label, items }, gi) => (
          <div
            key={label}
            className="animate-fade-up"
            style={{ animationDelay: `${180 + gi * 60}ms` }}
          >
            {/* group header */}
            <div className="mb-3 flex items-center gap-2.5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-vibrant">
                {label}
              </p>
              <span className="h-px flex-1 bg-gradient-to-r from-vibrant/15 to-transparent" />
            </div>

            {/* tool rows */}
            <div className="-mx-2.5 space-y-0.5">
              {items.map((t) => {
                const Icon = t.icon;
                return (
                  <Link
                    key={t.href}
                    href={t.href}
                    className="group flex items-center gap-3 rounded-editorial px-2.5 py-2.5 transition-colors hover:bg-brand-50/60"
                  >
                    <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-brand-50 text-vibrant transition-colors group-hover:bg-vibrant group-hover:text-white">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-foreground">
                        {t.title}
                      </span>
                      <span className="block text-sm leading-snug text-foreground/55">
                        {t.description}
                      </span>
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 flex-shrink-0 text-foreground/10 transition-colors group-hover:text-vibrant" />
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
