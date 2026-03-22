"use client";

import { CheckCircle2 } from "lucide-react";

const principles = [
  "Clear food and ingredient guidance",
  "One product for analysis and planning",
  "Saved history that stays usable over time",
];

const capabilities = [
  "Food analysis from text or image",
  "Ingredient checking",
  "Meal planning and recipes",
  "Quiz, chat, and calculator history",
];

export default function AboutPage() {
  return (
    <div className="bg-background pt-40 pb-20">
      <div className="mx-auto w-full max-w-[1440px] px-6 sm:px-10 lg:px-16">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1.1fr)_360px]">
          <section className="space-y-10">
            <header className="border-b border-black/[0.08] pb-8">
              <h1 className="text-6xl sm:text-7xl font-display leading-[0.95] text-foreground">
                About <span className="italic text-vibrant">Us</span>
              </h1>
              <p className="mt-6 max-w-2xl text-xl leading-relaxed text-foreground/60">
                NutriAI helps users move from food questions to clear daily decisions.
              </p>
            </header>

            <section className="grid gap-4 md:grid-cols-3">
              {principles.map((item) => (
                <div key={item} className="app-panel p-6">
                  <p className="text-base leading-7 text-foreground">{item}</p>
                </div>
              ))}
            </section>

            <section className="app-panel p-8">
              <h2 className="text-3xl font-display text-foreground">What the product covers</h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {capabilities.map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-1 h-4 w-4 text-vibrant" />
                    <span className="text-sm leading-6 text-foreground/70">{item}</span>
                  </div>
                ))}
              </div>
            </section>
          </section>

          <aside className="space-y-4">
            <div className="app-panel p-8">
              <h2 className="text-2xl font-display text-foreground">Platform</h2>
              <div className="mt-5 space-y-3 text-sm leading-6 text-foreground/70">
                <p>FastAPI handles processing and API delivery.</p>
                <p>Next.js powers the frontend experience.</p>
                <p>Convex stores saved records and history.</p>
                <p>Clerk manages sign in and identity.</p>
              </div>
            </div>

            <div className="app-panel p-8">
              <h2 className="text-2xl font-display text-foreground">Access</h2>
              <p className="mt-5 text-sm leading-6 text-foreground/70">
                About, Articles, and Docs are public. Dashboard tools are where signed-in users work with plans, history, and feature access.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
