"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import type { ComponentType } from "react";
import {
  Apple,
  ArrowRight,
  Brain,
  Calculator,
  Leaf,
  MessageSquare,
  MessageSquareMore,
  Microscope,
  Settings,
  ShieldCheck,
  Sparkles,
  Soup,
} from "lucide-react";

type FeatureCard = {
  title: string;
  description: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
  group: "Analyze" | "Plan" | "Refine" | "Track";
};

const features: FeatureCard[] = [
  {
    title: "Food Insight",
    description: "Analyze meals from text or image.",
    href: "/food-insight",
    icon: Brain,
    group: "Analyze",
  },
  {
    title: "Ingredient Checker",
    description: "Check ingredient safety and concerns.",
    href: "/ingredient-checker",
    icon: Microscope,
    group: "Analyze",
  },
  {
    title: "Nutri Quiz",
    description: "Test your nutrition knowledge.",
    href: "/nutri-quiz",
    icon: Sparkles,
    group: "Analyze",
  },
  {
    title: "Meal Planner",
    description: "Generate a daily meal plan.",
    href: "/meal-planner",
    icon: Leaf,
    group: "Plan",
  },
  {
    title: "Recipe Finder",
    description: "Get recipes and shopping links.",
    href: "/recipe-finder",
    icon: Soup,
    group: "Plan",
  },
  {
    title: "Recommendations",
    description: "Get personalized next steps.",
    href: "/recommendations",
    icon: Apple,
    group: "Refine",
  },
  {
    title: "Nutri Chat",
    description: "Ask questions and get quick help.",
    href: "/nutri-chat",
    icon: MessageSquare,
    group: "Refine",
  },
  {
    title: "Nutri Calc",
    description: "Track BMI and calories.",
    href: "/nutri-calc",
    icon: Calculator,
    group: "Track",
  },
  {
    title: "Library",
    description: "View all history and settings.",
    href: "/library",
    icon: Settings,
    group: "Track",
  },
  {
    title: "Subscription",
    description: "Manage your plan and feature access.",
    href: "/subscription",
    icon: ShieldCheck,
    group: "Track",
  },
];

const flow = ["Analyze", "Plan", "Refine", "Track"] as const;

const groupDescriptions: Record<(typeof flow)[number], string> = {
  Analyze: "Inspect meals, ingredients, and nutrition questions.",
  Plan: "Build meals, recipes, and next-step guidance.",
  Refine: "Turn answers into recommendations and follow-up support.",
  Track: "Review progress, saved work, and account details.",
};

export default function DashboardOverview() {
  const { user } = useUser();
  const firstName = user?.firstName?.trim();
  const primaryActions = features.slice(0, 4);
  const groupedFeatures = flow.map((group) => ({
    group,
    description: groupDescriptions[group],
    cards: features.filter((item) => item.group === group),
  }));

  return (
    <div className="mx-auto w-full max-w-[1200px] pb-10">
      <section className="rounded-editorial border border-black/[0.08] bg-white px-5 py-6 sm:px-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px] lg:items-start">
          <div>
            <p className="text-sm font-medium text-foreground/50">Dashboard</p>
            <h1 className="mt-2 text-3xl text-foreground sm:text-4xl">
              Welcome back{firstName ? `, ${firstName}` : ""}.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-foreground/65 sm:text-base">
              Choose a tool to analyze, plan, refine, or track your nutrition work. The most-used actions are surfaced first.
            </p>
          </div>

          <div className="rounded-editorial border border-black/[0.08] bg-stone-50 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-editorial border border-black/[0.08] bg-white text-vibrant">
                <MessageSquareMore className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <h2 className="text-base font-semibold text-foreground">Need a quick answer?</h2>
                <p className="mt-1 text-sm leading-6 text-foreground/60">
                  Open Nutri Chat for ingredient questions, meal ideas, or fast nutrition guidance.
                </p>
              </div>
            </div>
            <Link
              href="/nutri-chat"
              className="mt-4 inline-flex h-10 w-full items-center justify-center rounded-editorial bg-foreground px-4 text-sm font-medium text-white transition hover:bg-foreground/90"
            >
              Open Nutri Chat
            </Link>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.9fr)]">
        <div className="rounded-editorial border border-black/[0.08] bg-white p-5 sm:p-6">
          <div className="border-b border-black/[0.08] pb-4">
            <h2 className="text-lg font-semibold text-foreground">Start a task</h2>
            <p className="mt-1 text-sm text-foreground/60">
              Jump directly into the tools people usually open first.
            </p>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {primaryActions.map((feature) => {
              const Icon = feature.icon;
              return (
                <Link
                  key={feature.href}
                  href={feature.href}
                  className="group rounded-editorial border border-black/[0.08] bg-stone-50 px-4 py-4 transition hover:border-vibrant/25 hover:bg-white"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-editorial border border-black/[0.08] bg-white text-vibrant">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-foreground">{feature.title}</p>
                        <ArrowRight className="h-4 w-4 flex-shrink-0 text-foreground/35 transition-colors group-hover:text-vibrant" />
                      </div>
                      <p className="mt-1 text-sm leading-6 text-foreground/58">{feature.description}</p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="rounded-editorial border border-black/[0.08] bg-[#fcfbf8] p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-foreground">Workspace structure</h2>
          <p className="mt-1 text-sm leading-6 text-foreground/60">
            The dashboard is organized by what you are trying to do, not by visual category.
          </p>

          <div className="mt-5 space-y-3">
            {groupedFeatures.map(({ group, description, cards }) => (
              <div key={group} className="rounded-editorial border border-black/[0.08] bg-white px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-foreground">{group}</p>
                  <span className="text-xs text-foreground/45">{cards.length} tools</span>
                </div>
                <p className="mt-1 text-sm leading-6 text-foreground/58">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2">
        {groupedFeatures.map(({ group, cards, description }) => (
          <div key={group} className="rounded-editorial border border-black/[0.08] bg-white p-5 sm:p-6">
            <div className="flex items-start justify-between gap-4 border-b border-black/[0.08] pb-4">
              <div>
                <h2 className="text-lg font-semibold text-foreground">{group}</h2>
                <p className="mt-1 text-sm text-foreground/58">{description}</p>
              </div>
              <span className="text-sm text-foreground/40">{cards.length}</span>
            </div>

            <div className="mt-2 divide-y divide-black/[0.06]">
              {cards.map((feature) => {
                const Icon = feature.icon;
                return (
                  <Link
                    key={feature.href}
                    href={feature.href}
                    className="group flex items-start gap-4 py-4 transition-colors hover:text-foreground"
                  >
                    <div className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-editorial border border-black/[0.08] bg-stone-50 text-vibrant">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-foreground">{feature.title}</p>
                      <p className="mt-1 text-sm leading-6 text-foreground/58">{feature.description}</p>
                    </div>
                    <ArrowRight className="mt-1 h-4 w-4 flex-shrink-0 text-foreground/30 transition-colors group-hover:text-vibrant" />
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
