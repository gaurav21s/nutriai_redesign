"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import type { ComponentType } from "react";
import {
  Apple,
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

  return (
    <div className="space-y-8 pb-8">
      <section className="border-b border-black/[0.08] pb-4">
        <h1 className="text-3xl font-display text-foreground">
          Welcome{user?.firstName ? `, ${user.firstName}` : ""}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-foreground/65">Pick a feature to get started. Your history is saved in Library.</p>
      </section>

      <section className="space-y-6">
        {flow.map((group) => {
          const cards = features.filter((item) => item.group === group);
          if (!cards.length) return null;

          return (
            <div key={group} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="h-px w-8 bg-vibrant/40" />
                <h2 className="text-base font-display text-foreground">{group}</h2>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {cards.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <Link
                      key={feature.href}
                      href={feature.href}
                      className="app-panel group border-l-2 border-l-vibrant/80 p-5 hover:border-l-vibrant hover:bg-muted"
                    >
                      <div className="flex items-start gap-3">
                        <Icon className="mt-0.5 h-4 w-4 text-vibrant" />
                        <div>
                          <h3 className="text-base font-display text-foreground">
                            {feature.title}
                          </h3>
                          <p className="mt-1 text-sm text-foreground/65">{feature.description}</p>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
