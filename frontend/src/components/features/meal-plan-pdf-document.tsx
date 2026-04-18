"use client";

import { forwardRef } from "react";

import type { MealPlanGenerateRequest, MealPlanResponse } from "@/types/api";

export const MEAL_PLAN_PDF_WIDTH_PX = 794;

interface MealPlanPdfDocumentProps {
  age: number;
  fullName: string;
  generatedAt?: Date;
  mealPlan: MealPlanResponse;
  profile: MealPlanGenerateRequest;
}

const profileLabels: Array<{ key: keyof MealPlanGenerateRequest; label: string }> = [
  { key: "goal", label: "Goal" },
  { key: "diet_choice", label: "Diet" },
  { key: "food_type", label: "Cuisine" },
  { key: "gym", label: "Workout" },
  { key: "height", label: "Height" },
  { key: "weight", label: "Weight" },
  { key: "gender", label: "Gender" },
  { key: "issue", label: "Consideration" },
];

function splitCalories(option: string): { title: string; details?: string } {
  const match = option.match(/^(.*?)\s*(\([^)]*(?:calorie|calories|kcal)[^)]*\))\s*$/i);
  if (!match) return { title: option };
  return { title: match[1].trim(), details: match[2].replace(/^\(|\)$/g, "").trim() };
}

function formatDate(value: Date): string {
  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(value);
}

export const MealPlanPdfDocument = forwardRef<HTMLDivElement, MealPlanPdfDocumentProps>(
  ({ age, fullName, generatedAt = new Date(), mealPlan, profile }, ref) => {
    const displayName = fullName.trim() || "NutriAI User";
    const sections = mealPlan.sections.filter((section) => section.options.length);

    return (
      <div
        ref={ref}
        className="relative overflow-hidden bg-[#faf8f5] p-8 text-[#292524]"
        style={{
          width: MEAL_PLAN_PDF_WIDTH_PX,
          minHeight: 1123,
          fontFamily: '"IBM Plex Sans", "Aptos", "Helvetica Neue", sans-serif',
        }}
      >
        <div className="pointer-events-none absolute -right-16 top-44 rotate-90 text-[112px] font-black tracking-[-0.08em] text-[#f0e4d7]">
          NUTRIAI
        </div>
        <div className="pointer-events-none absolute left-[-120px] top-[-120px] h-80 w-80 rounded-full bg-[#fed7aa]/55 blur-3xl" />
        <div className="pointer-events-none absolute bottom-[-160px] right-[-120px] h-96 w-96 rounded-full bg-[#d97706]/15 blur-3xl" />

        <main className="relative z-10 border border-black/[0.08] bg-white shadow-[0_18px_60px_rgba(41,37,36,0.14)]">
          <section className="relative overflow-hidden bg-[#7c2d12] px-9 py-8 text-white">
            <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_80%_20%,rgba(251,146,60,0.55),transparent_34%),linear-gradient(135deg,transparent,rgba(255,247,237,0.08))]" />
            <div className="relative flex items-start justify-between gap-8">
              <div>
                <div className="inline-flex items-center gap-2 bg-[#d97706] px-4 py-2 text-[11px] font-black uppercase tracking-[0.22em]">
                  <span className="h-2 w-2 rounded-full bg-white" />
                  NutriAI
                </div>
                <h1 className="mt-7 max-w-[520px] text-[44px] font-black leading-[0.95] tracking-[-0.08em]">
                  Personalized Meal Plan
                </h1>
                <p className="mt-4 max-w-[460px] text-sm font-medium leading-6 text-orange-50/85">
                  A polished nutrition guide built around your goal, routine, diet preference, and practical daily meals.
                </p>
              </div>
              <div className="w-[150px] border border-white/20 bg-white/10 p-4 text-right backdrop-blur-sm">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-orange-100/80">Generated</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.05em]">{formatDate(generatedAt)}</p>
                <div className="mt-5 h-px bg-white/20" />
                <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.22em] text-orange-100/80">Plan ID</p>
                <p className="mt-1 text-xs font-semibold text-orange-50/80">{mealPlan.id.slice(0, 8).toUpperCase()}</p>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-[1fr_1.45fr] gap-5 border-b border-black/[0.08] bg-[#fff7ed] px-9 py-6">
            <div className="bg-white p-5 shadow-[inset_0_0_0_1px_rgba(41,37,36,0.08)]">
              <p className="text-[10px] font-black uppercase tracking-[0.24em] text-[#b45309]">Prepared For</p>
              <p className="mt-3 text-3xl font-black tracking-[-0.06em]">{displayName}</p>
              <p className="mt-2 text-sm font-semibold text-[#78716c]">Age {age || "-"} · {profile.gender || "Profile"}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white p-4 shadow-[inset_0_0_0_1px_rgba(41,37,36,0.08)]">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#b45309]">Main Goal</p>
                <p className="mt-2 text-xl font-black tracking-[-0.04em]">{profile.goal || "-"}</p>
              </div>
              <div className="bg-white p-4 shadow-[inset_0_0_0_1px_rgba(41,37,36,0.08)]">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#b45309]">Food Style</p>
                <p className="mt-2 text-xl font-black tracking-[-0.04em]">{profile.diet_choice || "-"}</p>
              </div>
              <div className="col-span-2 bg-[#292524] p-4 text-white">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-orange-200">NutriAI Guidance</p>
                <p className="mt-2 text-sm leading-5 text-white/80">
                  Follow this as a flexible structure. Keep portions consistent, hydrate well, and adjust ingredients to your medical needs or local availability.
                </p>
              </div>
            </div>
          </section>

          <section className="px-9 py-7">
            <div className="flex items-end justify-between border-b border-black/[0.08] pb-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.26em] text-[#d97706]">Profile Snapshot</p>
                <h2 className="mt-1 text-2xl font-black tracking-[-0.06em]">Your nutrition inputs</h2>
              </div>
              <p className="text-right text-xs font-semibold leading-5 text-[#78716c]">
                Warm Indian-inspired palette
                <br />
                Website themed export
              </p>
            </div>

            <div className="mt-5 grid grid-cols-4 gap-3">
              {profileLabels.map((item) => (
                <div key={item.key} className="border border-black/[0.08] bg-[#faf8f5] p-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.18em] text-[#b45309]">{item.label}</p>
                  <p className="mt-2 min-h-8 text-[13px] font-bold leading-4 text-[#292524]">{profile[item.key] || "-"}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="px-9 pb-9">
            <div className="mb-5 flex items-center gap-3">
              <div className="h-9 w-1 bg-[#d97706]" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.24em] text-[#d97706]">Daily Plan</p>
                <h2 className="text-2xl font-black tracking-[-0.06em]">Meal structure</h2>
              </div>
            </div>

            <div className="space-y-5">
              {sections.map((section, sectionIndex) => (
                <article key={`${section.name}-${sectionIndex}`} className="overflow-hidden border border-black/[0.08] bg-white">
                  <header className="flex items-center justify-between bg-[#f3e7d3] px-5 py-4">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.24em] text-[#b45309]">
                        Meal {String(sectionIndex + 1).padStart(2, "0")}
                      </p>
                      <h3 className="mt-1 text-2xl font-black tracking-[-0.06em]">{section.name}</h3>
                    </div>
                    <div className="rounded-full bg-white px-4 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-[#b45309]">
                      {section.options.length} options
                    </div>
                  </header>

                  <div className="grid gap-3 p-5">
                    {section.options.map((option, optionIndex) => {
                      const parsed = splitCalories(option);
                      return (
                        <div
                          key={`${section.name}-${optionIndex}`}
                          className="grid grid-cols-[42px_1fr] gap-4 border-l-4 border-[#d97706] bg-[#faf8f5] p-4"
                        >
                          <div className="flex h-10 w-10 items-center justify-center bg-[#292524] text-sm font-black text-white">
                            {String(optionIndex + 1).padStart(2, "0")}
                          </div>
                          <div>
                            <p className="text-[15px] font-black leading-5 tracking-[-0.02em] text-[#292524]">
                              {parsed.title}
                            </p>
                            {parsed.details ? (
                              <p className="mt-2 text-[12px] font-semibold leading-5 text-[#78716c]">{parsed.details}</p>
                            ) : null}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="mx-9 mb-9 grid grid-cols-[1fr_180px] gap-5 bg-[#292524] p-5 text-white">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.24em] text-orange-200">Final Note</p>
              <p className="mt-2 text-sm leading-6 text-white/80">
                This PDF is generated by NutriAI for planning and education. For allergies, chronic conditions, pregnancy, or strict clinical targets, confirm changes with a qualified professional.
              </p>
            </div>
            <div className="border border-white/15 p-4 text-right">
              <p className="text-[10px] font-black uppercase tracking-[0.22em] text-orange-200">Watermark</p>
              <p className="mt-2 text-2xl font-black tracking-[-0.08em]">NUTRIAI</p>
            </div>
          </section>
        </main>
      </div>
    );
  }
);

MealPlanPdfDocument.displayName = "MealPlanPdfDocument";
