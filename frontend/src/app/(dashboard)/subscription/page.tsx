"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Sparkles, CreditCard, ShieldCheck, Activity, ArrowRight } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import type {
  CurrencyCode,
  PlanSummary,
  PlanTier,
  SubscriptionEvent,
  SubscriptionRecord,
} from "@/types/api";

function priceValue(plan: PlanSummary, currency: CurrencyCode): string {
  const amount = currency === "USD" ? plan.price_usd.amount : plan.price_inr.amount;
  if (amount === 0) return "Free";
  return `${currency === "USD" ? "$" : "₹"}${amount.toLocaleString("en-IN")}`;
}

export default function SubscriptionPage() {
  const api = useApiClient();

  const [currency, setCurrency] = useState<CurrencyCode>("USD");
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [current, setCurrent] = useState<SubscriptionRecord | null>(null);
  const [events, setEvents] = useState<SubscriptionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutStatus, setCheckoutStatus] = useState<string | null>(null);

  const loadAction = useAsyncAction(async () => {
    const [catalog, active, history] = await Promise.all([
      api.getPricingPlans(),
      api.getCurrentSubscription(),
      api.getSubscriptionHistory(60),
    ]);
    return { plans: catalog.plans, subscription: active.subscription, history };
  });

  const chooseAction = useAsyncAction(async (tier: PlanTier) => {
    if (tier === "free") {
      return api.selectSubscriptionPlan(tier, currency);
    }

    const origin = window.location.origin;
    const checkout = await api.createCheckoutSession({
      tier,
      currency,
      success_url: `${origin}/subscription?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/subscription?checkout=cancelled`,
    });

    window.location.href = checkout.checkout_url;
    return null;
  });

  async function refresh() {
    setLoading(true);
    setError(null);
    const result = await loadAction.execute();
    if (!result) {
      setLoading(false);
      return;
    }

    setPlans(result.plans);
    setCurrent(result.subscription);
    setEvents(result.history);
    setLoading(false);
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (loadAction.error) setError(loadAction.error);
  }, [loadAction.error]);

  useEffect(() => {
    if (chooseAction.error) setError(chooseAction.error);
  }, [chooseAction.error]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("checkout");
    const sessionId = params.get("session_id");

    setCheckoutStatus(status);

    if (status !== "success" || !sessionId) return;
    const confirmedSessionId = sessionId;

    let mounted = true;

    async function confirm() {
      try {
        await api.confirmCheckoutSession(confirmedSessionId);
        if (mounted) {
          await refresh();
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Checkout confirmation failed");
        }
      }
    }

    void confirm();

    return () => {
      mounted = false;
    };
  }, [api]);

  const sortedPermissions = useMemo(() => {
    const permissions = current?.permissions ?? {};
    return Object.entries(permissions).sort(([a], [b]) => a.localeCompare(b));
  }, [current]);

  return (
    <FeatureShell
      title="Subscription"
      description="Manage your plan and view billing history."
      aside={
        <HistoryPanel
          title="Billing Events"
          loading={loading}
          empty={!events.length}
          syncing={chooseAction.loading}
        >
          {events.map((event) => (
            <div key={event.id} className="rounded-editorial border border-black/[0.03] bg-white/40 p-4 shadow-soft-glow mb-3 group hover:border-vibrant/20 transition-all">
              <div className="flex items-center gap-3 mb-1">
                <Activity className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-foreground group-hover:text-vibrant transition-colors">{event.event_type.replaceAll("_", " ")}</p>
              </div>
              <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/20 italic">{new Date(event.created_at).toLocaleString()}</p>
            </div>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-12">
        {error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant font-medium italic">{error}</Alert> : null}

        {checkoutStatus === "success" && (
          <Alert variant="success" className="rounded-2xl bg-success-50 border-success-500/10 text-success-700 animate-pulse">Checkout complete. Your plan is being updated.</Alert>
        )}

        <div className="grid gap-8 grid-cols-1 lg:grid-cols-12 items-start">
          <Card className="lg:col-span-12 border border-black/[0.03] bg-white/60 shadow-elegant overflow-hidden relative">
            <div className="absolute top-0 right-0 p-10 opacity-[0.03] pointer-events-none">
              <ShieldCheck className="h-32 w-32" />
            </div>
            <CardHeader className="p-10 border-b border-black/[0.03] bg-black/[0.01]">
              <div className="flex items-center gap-3 text-vibrant font-semibold tracking-widest uppercase text-[10px] mb-4">
                <Sparkles className="h-3.5 w-3.5" />
                Current Plan
              </div>
              <div className="flex flex-wrap items-end justify-between gap-6">
                <div>
                  <CardTitle className="text-5xl font-display mb-2">{current?.tier.toUpperCase() ?? "FREE"}</CardTitle>
                  <CardDescription className="text-sm font-medium italic text-foreground/40 leading-relaxed">
                    {current?.status === "active" ? "Your plan is active." : "Limited access mode."}
                  </CardDescription>
                </div>
                <div className="flex gap-4">
                  <div className="px-6 py-2 rounded-full bg-white/80 border border-black/[0.05] shadow-soft-glow">
                    <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/30 mb-1">Status</p>
                    <p className="text-sm font-bold text-success-600">{current?.status ?? "active"}</p>
                  </div>
                  <div className="px-6 py-2 rounded-full bg-white/80 border border-black/[0.05] shadow-soft-glow">
                    <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/30 mb-1">Fee</p>
                    <p className="text-sm font-bold text-foreground">{current ? `${current.currency} ${current.amount}/mo` : "FREE"}</p>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-10 space-y-10">
              <div>
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-foreground/30 mb-6 border-b border-black/[0.02] pb-3">Available Permissions</h4>
                <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-4">
                  {sortedPermissions.map(([key, enabled]) => (
                    <div key={key} className={`flex items-center gap-3 rounded-full border px-6 py-3 transition-all ${enabled ? "bg-white/80 border-black/[0.05] shadow-sm text-foreground/80" : "bg-black/[0.02] border-transparent text-foreground/20 italic opacity-60"
                      }`}>
                      <div className={`h-2 h-2 rounded-full ${enabled ? "bg-vibrant/60" : "bg-foreground/20"}`} />
                      <span className="text-[10px] font-bold uppercase tracking-widest">{key.replaceAll("_", " ")}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button variant="outline" className="rounded-full border-black/[0.05] hover:bg-black/[0.02] text-[10px] font-bold uppercase tracking-widest px-8" onClick={() => void refresh()}>
                  Refresh
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-12 border border-black/[0.03] bg-white/40 shadow-soft-glow">
            <CardHeader className="p-10 border-b border-black/0.02">
              <CardTitle className="text-3xl font-display">Choose Plan</CardTitle>
              <CardDescription className="text-sm font-medium text-foreground/40 italic">Pick a monthly plan.</CardDescription>
            </CardHeader>
            <CardContent className="p-10 space-y-12">
              <div className="max-w-[300px]">
                <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-foreground/40">Currency</p>
                <Select value={currency} className="bg-white/60 border-black/[0.05] rounded-full h-12 shadow-sm" onChange={(e) => setCurrency(e.target.value as CurrencyCode)}>
                  <option value="USD">United States Dollar (USD)</option>
                  <option value="INR">Indian Rupee (INR)</option>
                </Select>
              </div>

              <div className="grid gap-8 lg:grid-cols-3">
                {plans.map((plan) => {
                  const active = current?.tier === plan.tier;
                  const isRecommended = plan.recommended;
                  return (
                    <div
                      key={plan.tier}
                      className={`rounded-editorial border p-8 flex flex-col justify-between transition-all duration-700 relative overflow-hidden group ${active ? "bg-white/20 border-vibrant/30 opacity-60" :
                          isRecommended ? "bg-white/80 border-vibrant/20 shadow-elegant" : "bg-white/60 border-black/[0.03] shadow-soft-glow hover:border-vibrant/10"
                        }`}
                    >
                      {isRecommended && !active && (
                        <div className="absolute top-0 left-0 right-0 h-1 bg-vibrant" />
                      )}
                      <div>
                        <div className="flex justify-between items-start mb-6">
                          <p className={`text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border ${isRecommended ? "bg-vibrant/5 border-vibrant/20 text-vibrant" : "bg-black/5 border-transparent text-foreground/40 font-medium"
                            }`}>{plan.label}</p>
                          {active && <ShieldCheck className="h-4 w-4 text-vibrant/60" />}
                        </div>
                        <div className="flex items-baseline gap-2 mb-4">
                          <p className="text-4xl font-display font-semibold text-foreground group-hover:text-vibrant transition-colors">{priceValue(plan, currency)}</p>
                          <span className="text-xs font-medium text-foreground/30 italic">/mo</span>
                        </div>
                        <p className="text-xs text-foreground/50 font-medium mb-8 leading-relaxed italic">{plan.description}</p>

                        <ul className="space-y-4 mb-10">
                          {plan.features.map((feature) => (
                            <li key={feature} className="flex items-start gap-4 text-[11px] font-semibold text-foreground/70 uppercase tracking-widest">
                              <div className={`mt-0.5 h-2 w-2 rounded-full ${isRecommended ? "bg-vibrant/60" : "bg-foreground/10"}`} />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <Button
                        className={`w-full h-12 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${active ? "bg-black/[0.05] text-foreground/20 cursor-default" :
                            isRecommended ? "bg-vibrant text-white hover:bg-vibrant/90 shadow-soft-glow" : "bg-foreground text-background hover:bg-foreground/90 shadow-sm"
                          }`}
                        disabled={chooseAction.loading || active}
                        onClick={() => void chooseAction.execute(plan.tier)}
                      >
                        {active ? "Current Plan" : plan.tier === "free" ? "Switch to Free" : `Choose ${plan.label}`}
                      </Button>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </FeatureShell>
  );
}
