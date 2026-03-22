"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { SignInButton, SignedIn, SignedOut, useUser } from "@clerk/nextjs";
import { Check, Sparkles, ArrowRight } from "lucide-react";
import { motion, type Variants } from "framer-motion";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import type { CurrencyCode, PlanSummary, PlanTier, SubscriptionRecord } from "@/types/api";

function formatPrice(plan: PlanSummary, currency: CurrencyCode): string {
  const amount = currency === "USD" ? plan.price_usd.amount : plan.price_inr.amount;
  const symbol = currency === "USD" ? "$" : "₹";
  if (amount === 0) return "Free";
  return `${symbol}${amount.toLocaleString("en-IN")}`;
}

const container: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.8,
      ease: [0.19, 1, 0.22, 1]
    }
  },
};

export default function PricingPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [current, setCurrent] = useState<SubscriptionRecord | null>(null);
  const [currency, setCurrency] = useState<CurrencyCode>("USD");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const subscribeAction = useAsyncAction(async (tier: PlanTier) => {
    if (tier === "free") {
      return api.selectSubscriptionPlan(tier, currency);
    }

    const origin = window.location.origin;
    const checkout = await api.createCheckoutSession({
      tier,
      currency,
      success_url: `${origin}/subscription?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/pricing?checkout=cancelled`,
    });

    window.location.href = checkout.checkout_url;
    return null;
  });

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const catalog = await api.getPricingPlans();
        let subscription: SubscriptionRecord | null = null;
        try {
          const currentPlan = await api.getCurrentSubscription();
          subscription = currentPlan.subscription;
        } catch {
          subscription = null;
        }
        if (!mounted) return;
        setPlans(catalog.plans);
        setCurrent(subscription);
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load pricing");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [api]);

  return (
    <div className="bg-background min-h-screen pt-40 pb-32">
      <div className="mx-auto w-full max-w-[1440px] px-6 sm:px-10 lg:px-16">
        <header className="mb-24 flex flex-col md:flex-row md:items-end justify-between gap-12">
          <div className="max-w-2xl">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 flex items-center gap-3 text-vibrant font-semibold tracking-widest uppercase text-[10px]"
            >
              <div className="h-[1px] w-12 bg-vibrant/30" />
              NutriAI Excellence
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-6xl sm:text-7xl font-display leading-tight mb-8"
            >
              Choose <br /> <span className="italic text-vibrant">your</span> Plan.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-foreground/60 leading-relaxed font-medium"
            >
              Simple monthly pricing in USD and INR.
              Pick the plan that fits your needs.
            </motion.p>
          </div>

          <div className="w-full max-w-[280px]">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-foreground/40">Select Currency</p>
            <div className="relative group">
              <Select
                value={currency}
                onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
                className="w-full bg-white/60 border-black/[0.05] rounded-full h-14 pl-6 text-sm font-semibold tracking-wider appearance-none focus:border-vibrant transition-all"
              >
                <option value="USD">United States Dollar (USD)</option>
                <option value="INR">Indian Rupee (INR)</option>
              </Select>
              <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-foreground/20 group-hover:text-vibrant transition-colors">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>
            </div>
          </div>
        </header>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-12">
            <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{error}</Alert>
          </motion.div>
        )}

        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid gap-8 md:grid-cols-3"
        >
          {loading ? (
            [1, 2, 3].map((idx) => (
              <div key={idx} className="h-[600px] rounded-editorial bg-black/[0.02] animate-pulse" />
            ))
          ) : (
            plans.map((plan) => {
              const active = current?.tier === plan.tier;
              const isRecommended = plan.recommended;

              return (
                <motion.div key={plan.tier} variants={item}>
                  <Card className={`h-full group transition-all duration-700 overflow-hidden relative ${isRecommended
                    ? "bg-white/80 border-vibrant/20 shadow-elegant"
                    : "bg-white/40 border-black/[0.03] shadow-soft-glow hover:border-vibrant/10"
                    }`}>
                    {isRecommended && (
                      <div className="absolute top-0 right-0 left-0 h-1.5 bg-vibrant" />
                    )}

                    <CardHeader className="p-10 pb-0">
                      <div className="flex items-center justify-between mb-8">
                        <span className={`text-[10px] font-bold uppercase tracking-widest px-4 py-1.5 rounded-full border ${isRecommended ? "bg-vibrant/5 border-vibrant/20 text-vibrant" : "bg-black/5 border-transparent text-foreground/40"
                          }`}>
                          {plan.label}
                        </span>
                        {isRecommended && <Sparkles className="h-5 w-5 text-vibrant animate-pulse" />}
                      </div>

                      <div className="mb-6">
                        <div className="text-5xl font-display mb-2 flex items-baseline gap-2">
                          {formatPrice(plan, currency)}
                          <span className="text-lg font-medium text-foreground/40 italic">/mo</span>
                        </div>
                        <p className="text-sm text-foreground/50 leading-relaxed font-medium italic">
                          {plan.description}
                        </p>
                      </div>
                    </CardHeader>

                    <CardContent className="p-10 pt-8 space-y-12">
                      <ul className="space-y-4">
                        {plan.features.map((feature) => (
                          <li key={feature} className="flex items-start gap-4 text-sm font-medium text-foreground/70">
                            <div className={`mt-1 flex h-4 w-4 items-center justify-center rounded-full border ${isRecommended ? "border-vibrant bg-vibrant text-white" : "border-black/10 bg-black/5 text-foreground/40"
                              }`}>
                              <Check className="h-2.5 w-2.5" />
                            </div>
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>

                      <div className="pt-8">
                        <SignedIn>
                          <Button
                            className={`w-full h-14 rounded-full text-xs font-bold uppercase tracking-widest transition-all duration-500 overflow-hidden relative group ${active ? "bg-black/5 text-foreground/30 pointer-events-none" :
                              isRecommended ? "bg-vibrant text-white hover:bg-vibrant/90 shadow-soft-glow" : "bg-foreground text-background hover:bg-foreground/90"
                              }`}
                            disabled={subscribeAction.loading || active}
                            onClick={() => void subscribeAction.execute(plan.tier)}
                          >
                            <span className="relative z-10">
                              {active ? "Current Plan" : plan.tier === "free" ? "Switch to Free" : `Choose ${plan.label}`}
                            </span>
                          </Button>
                        </SignedIn>
                        <SignedOut>
                          <SignInButton mode="modal">
                            <Button className={`w-full h-14 rounded-full text-xs font-bold uppercase tracking-widest ${isRecommended ? "bg-vibrant text-white hover:bg-vibrant/90" : "bg-foreground text-background hover:bg-foreground/90"
                              }`}>
                              Sign In To Continue
                            </Button>
                          </SignInButton>
                        </SignedOut>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })
          )}
        </motion.div>

        <footer className="mt-24 border-t border-black/[0.03] pt-12 flex flex-col md:flex-row items-center justify-between gap-8">
          <p className="text-[10px] font-bold uppercase tracking-widest text-foreground/30">
            All plans include secure billing and account protection.
          </p>
          <Link href="/subscription" className="text-[10px] font-bold uppercase tracking-widest text-vibrant hover:underline underline-offset-4 decoration-2">
            Manage Active Subscription
          </Link>
        </footer>
      </div>
    </div>
  );
}
