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
  Microscope,
  Plus,
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

export default function DashboardOverview() {
  const { user } = useUser();
  const firstName = user?.firstName?.trim();
  const primaryActions = features.slice(0, 4);

  return (
    <div className="relative overflow-hidden rounded-[34px] border border-black/[0.06] bg-[radial-gradient(circle_at_top,rgba(245,158,11,0.08),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.82),rgba(255,255,255,0.96))] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-150px)] w-full max-w-[1120px] flex-col justify-center pb-8 pt-4">
        <section className="mx-auto w-full max-w-[840px] text-center">
          <p className="text-sm font-medium text-foreground/45">NutriAI workspace</p>
          <h1 className="mt-5 text-4xl font-display leading-tight text-foreground sm:text-5xl lg:text-6xl">
            Ready when you are{firstName ? `, ${firstName}` : ""}.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-foreground/60 sm:text-lg">
            Start with a nutrition task, jump into a saved workflow, or pick a tool below to keep momentum going.
          </p>
        </section>

        <section className="mx-auto mt-10 w-full max-w-[920px]">
          <div className="rounded-[32px] border border-black/[0.06] bg-white/92 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.08)] backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl bg-[rgb(255,247,237)] text-vibrant">
                <Plus className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1 text-left">
                <p className="text-base font-medium text-foreground/80 sm:text-lg">What would you like to do today?</p>
                <p className="text-sm text-foreground/45">Choose a tool and jump straight into analysis, planning, or tracking.</p>
              </div>
              <Link
                href="/nutri-chat"
                className="hidden h-11 items-center rounded-full bg-vibrant px-5 text-sm font-medium text-white transition hover:bg-vibrant/90 sm:inline-flex"
              >
                Open Nutri Chat
              </Link>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {primaryActions.map((feature) => {
                const Icon = feature.icon;
                return (
                  <Link
                    key={feature.href}
                    href={feature.href}
                    className="inline-flex items-center gap-2 rounded-full border border-black/[0.08] bg-background px-4 py-2.5 text-sm text-foreground/75 transition hover:border-vibrant/25 hover:text-foreground"
                  >
                    <Icon className="h-4 w-4 text-vibrant" />
                    {feature.title}
                  </Link>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mt-8">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {flow.map((group) => {
              const cards = features.filter((item) => item.group === group);
              return (
                <div key={group} className="rounded-[28px] border border-black/[0.06] bg-white/78 p-4 backdrop-blur">
                  <div className="mb-4 flex items-center gap-3">
                    <div className="h-px flex-1 bg-black/[0.08]" />
                    <h2 className="text-sm font-display text-foreground">{group}</h2>
                  </div>
                  <div className="space-y-2">
                    {cards.map((feature) => {
                      const Icon = feature.icon;
                      return (
                        <Link
                          key={feature.href}
                          href={feature.href}
                          className="group flex items-center gap-3 rounded-2xl px-3 py-3 transition hover:bg-[rgb(255,247,237)]"
                        >
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-[rgb(255,247,237)] text-vibrant">
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0 flex-1 text-left">
                            <p className="text-sm font-medium text-foreground">{feature.title}</p>
                            <p className="truncate text-xs text-foreground/50">{feature.description}</p>
                          </div>
                          <ArrowRight className="h-4 w-4 text-foreground/25 transition group-hover:translate-x-0.5 group-hover:text-vibrant" />
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
