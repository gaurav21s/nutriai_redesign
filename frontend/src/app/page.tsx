import Link from "next/link";
import {
  ArrowRight,
  Brain,
  ChartNoAxesCombined,
  Compass,
  CalendarCheck,
  CookingPot,
  FlaskConical,
  MessageCircleMore,
  MessageCircle,
  Search,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const tools = [
  {
    title: "Food Insight",
    description: "Text or image nutrition analysis.",
    icon: FlaskConical,
    href: "/food-insight",
  },
  {
    title: "Ingredient Checker",
    description: "Good vs risky ingredients at a glance.",
    icon: Search,
    href: "/ingredient-checker",
  },
  {
    title: "Meal Planner",
    description: "Goal-based meal structure.",
    icon: CalendarCheck,
    href: "/meal-planner",
  },
  {
    title: "Recipe Finder",
    description: "Recipes plus shopping links.",
    icon: CookingPot,
    href: "/recipe-finder",
  },
  {
    title: "Nutri Quiz",
    description: "Quick learning sessions.",
    icon: Brain,
    href: "/nutri-quiz",
  },
  {
    title: "Nutri Chat",
    description: "Ask and continue context.",
    icon: MessageCircleMore,
    href: "/nutri-chat",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-[1480px] px-4 pb-24 pt-12 sm:px-6 lg:px-8">
      <section className="relative overflow-hidden rounded-[2.5rem] border border-accent-200/65 bg-white/88 px-7 py-12 shadow-card sm:px-12 sm:py-16">
        <div className="pointer-events-none absolute -right-10 -top-10 h-56 w-56 rounded-full bg-brand-100/55 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-14 left-1/3 h-44 w-44 rounded-full bg-secondary-100/55 blur-2xl" />

        <div className="space-y-8">
          <p className="inline-flex items-center gap-2 rounded-full border border-accent-200/75 bg-surface-50 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent-700">
            <Sparkles className="h-3.5 w-3.5 text-secondary-600" />
            NutriAI Platform
          </p>

          <div className="space-y-4">
            <h1 className="max-w-4xl text-5xl font-semibold text-accent-900 sm:text-6xl lg:text-7xl">
              Better nutrition decisions. Less noise.
            </h1>
            <p className="max-w-2xl text-base text-accent-700 sm:text-lg">
              One focused workspace for analysis, planning, and execution.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link href="/food-insight">
              <Button size="lg" className="gap-2">
                Open Dashboard
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="ghost">
                API & Docs
              </Button>
            </Link>
          </div>

          <div className="grid gap-3 pt-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-accent-200/70 bg-surface-50/80 px-4 py-3">
              <p className="text-2xl font-semibold text-accent-900">11</p>
              <p className="text-xs uppercase tracking-[0.16em] text-accent-600">Modules</p>
            </div>
            <div className="rounded-2xl border border-accent-200/70 bg-surface-50/80 px-4 py-3">
              <p className="text-2xl font-semibold text-accent-900">Fast</p>
              <p className="text-xs uppercase tracking-[0.16em] text-accent-600">Background Processing</p>
            </div>
            <div className="rounded-2xl border border-accent-200/70 bg-surface-50/80 px-4 py-3">
              <p className="text-2xl font-semibold text-accent-900">Convex</p>
              <p className="text-xs uppercase tracking-[0.16em] text-accent-600">Per-user History</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-16 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-accent-200/70 bg-white/90">
          <CardHeader className="border-0 pb-2">
            <CardTitle className="text-3xl">Workflow First</CardTitle>
          </CardHeader>
          <CardContent className="pt-1">
            <div className="grid gap-3 sm:grid-cols-2">
              <Link href="/food-insight" className="rounded-2xl border border-accent-200/70 bg-surface-50 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.16em] text-accent-500">Step 1</p>
                <p className="mt-1 text-base font-semibold text-accent-900">Analyze</p>
                <p className="text-sm text-accent-700">Food Insight + Ingredient Checker</p>
              </Link>
              <Link href="/meal-planner" className="rounded-2xl border border-accent-200/70 bg-surface-50 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.16em] text-accent-500">Step 2</p>
                <p className="mt-1 text-base font-semibold text-accent-900">Plan</p>
                <p className="text-sm text-accent-700">Meal Planner + Recipes</p>
              </Link>
              <Link href="/nutri-chat" className="rounded-2xl border border-accent-200/70 bg-surface-50 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.16em] text-accent-500">Step 3</p>
                <p className="mt-1 text-base font-semibold text-accent-900">Refine</p>
                <p className="text-sm text-accent-700">Nutri Chat + Recommendations</p>
              </Link>
              <Link href="/nutri-quiz" className="rounded-2xl border border-accent-200/70 bg-surface-50 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.16em] text-accent-500">Step 4</p>
                <p className="mt-1 text-base font-semibold text-accent-900">Track</p>
                <p className="text-sm text-accent-700">Quiz + Calculator + History</p>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card className="border-brand-200/80 bg-gradient-to-br from-brand-50/80 via-white to-surface-50">
          <CardHeader className="border-0 pb-2">
            <CardTitle className="text-3xl">Live Stack</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-0 text-sm text-accent-700">
            <p className="flex items-center gap-2">
              <Compass className="h-4 w-4 text-secondary-600" />
              FastAPI `/api/v1` backend
            </p>
            <p className="flex items-center gap-2">
              <ChartNoAxesCombined className="h-4 w-4 text-secondary-600" />
              Convex persistence + history
            </p>
            <p className="flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-secondary-600" />
              Clerk-authenticated workspace
            </p>
            <div className="pt-2">
              <Link href="/food-insight">
                <Button variant="secondary" size="sm" className="gap-2">
                  Enter Workspace
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mt-16">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-3xl font-semibold text-accent-900 sm:text-4xl">Core Tools</h2>
          <Link href="/articles" className="text-sm font-semibold text-accent-700 hover:text-accent-900">
            Articles
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool, index) => {
            const Icon = tool.icon;
            return (
              <Link key={tool.title} href={tool.href}>
                <Card
                  className="h-full animate-fade-up border-accent-200/70 bg-white/90 transition hover:-translate-y-1 hover:border-brand-300 hover:shadow-soft"
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <CardHeader className="border-0 pb-2">
                    <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-surface-50 text-secondary-600">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-2xl">{tool.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-sm text-accent-700">{tool.description}</p>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
