"use client";

import { ReactNode, useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { Lock, Menu, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import Link from "next/link";
import { SignInButton, useUser } from "@clerk/nextjs";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useApiClient } from "@/hooks/useApiClient";
import { Sidebar } from "@/components/layout/sidebar";
import { cn } from "@/lib/cn";

const pathPermissionMap: Array<{ prefix: string; permission: string }> = [
  { prefix: "/food-insight", permission: "food_insight" },
  { prefix: "/ingredient-checker", permission: "ingredient_checker" },
  { prefix: "/meal-planner", permission: "meal_planner" },
  { prefix: "/recipe-finder", permission: "recipe_finder" },
  { prefix: "/nutri-chat", permission: "nutri_chat" },
  { prefix: "/nutri-quiz", permission: "nutri_quiz" },
  { prefix: "/nutri-calc", permission: "nutri_calc" },
  { prefix: "/recommendations", permission: "recommendations" },
];

function resolveRequiredPermission(pathname: string): string | null {
  const row = pathPermissionMap.find((item) => pathname.startsWith(item.prefix));
  return row ? row.permission : null;
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [permissions, setPermissions] = useState<Record<string, boolean> | null>(null);
  const [loadingPermissions, setLoadingPermissions] = useState(true);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const pathname = usePathname();
  const api = useApiClient();

  useEffect(() => {
    const stored = window.localStorage.getItem("nutriai.sidebar.collapsed");
    if (stored === "true") {
      setSidebarCollapsed(true);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("nutriai.sidebar.collapsed", String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    let active = true;

    async function loadPermissions() {
      setLoadingPermissions(true);
      setPermissionError(null);
      try {
        const current = await api.getCurrentSubscription();
        if (!active) return;
        setPermissions(current.subscription.permissions ?? {});
      } catch (err) {
        if (!active) return;
        setPermissions({});
        setPermissionError(err instanceof Error ? err.message : "Unable to verify subscription permissions");
      } finally {
        if (active) {
          setLoadingPermissions(false);
        }
      }
    }

    void loadPermissions();
    return () => {
      active = false;
    };
  }, [api]);

  const requiredPermission = useMemo(() => resolveRequiredPermission(pathname), [pathname]);
  const hasPermissionData = permissions !== null && !permissionError;
  const blockedByPlan = Boolean(
    requiredPermission && !loadingPermissions && hasPermissionData && permissions?.[requiredPermission] === false
  );

  if (isLoaded && !isSignedIn) {
    return (
      <div className="min-h-screen bg-background pt-14">
        <div className="mx-auto max-w-[720px] px-4 py-12 sm:px-6 lg:px-8">
          <section className="app-panel p-8">
            <h1 className="text-2xl font-display text-foreground">Sign in required</h1>
            <p className="mt-2 max-w-md text-sm text-foreground/65">
              Sign in to open your dashboard and use NutriAI tools.
            </p>
            <div className="mt-6">
              <SignInButton mode="modal">
                <Button size="sm">Sign in</Button>
              </SignInButton>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="mx-auto max-w-[1280px] px-4 py-6 sm:px-6 lg:px-8">
        <section className="mb-6 flex items-center justify-between border-b border-black/[0.08] pb-4">
          <button
            type="button"
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="inline-flex items-center gap-2 border border-black/[0.12] bg-white px-3 py-2 text-sm text-foreground hover:bg-muted xl:hidden"
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            {sidebarOpen ? "Close menu" : "Open menu"}
          </button>
          <div className="hidden items-center gap-3 xl:flex">
            <button
              type="button"
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              className="inline-flex items-center gap-2 border border-black/[0.12] bg-white px-3 py-2 text-sm text-foreground hover:bg-muted"
            >
              {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4 text-vibrant" /> : <PanelLeftClose className="h-4 w-4 text-vibrant" />}
              {sidebarCollapsed ? "Open sidebar" : "Close sidebar"}
            </button>
            <div className="text-sm text-foreground/55">Tools and history</div>
          </div>
        </section>

        {sidebarOpen ? (
          <div
            className="fixed inset-0 z-40 bg-black/20 xl:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}

        <div className={cn("grid gap-6", sidebarCollapsed ? "xl:grid-cols-[72px_minmax(0,1fr)]" : "xl:grid-cols-[252px_minmax(0,1fr)]")}>
          <div className="hidden xl:block">
            <Sidebar permissions={permissions} collapsed={sidebarCollapsed} />
          </div>

          {sidebarOpen ? (
            <div className="fixed left-0 top-0 z-50 h-screen w-[252px] overflow-y-auto bg-white xl:hidden">
              <div className="flex h-14 items-center justify-end border-b border-black/[0.08] px-4">
                <button onClick={() => setSidebarOpen(false)} className="text-foreground/55 hover:text-foreground">
                  <X className="h-6 w-6" />
                </button>
              </div>
              <Sidebar onNavigate={() => setSidebarOpen(false)} permissions={permissions} />
            </div>
          ) : null}

          <main className="min-w-0">
            {permissionError ? <Alert variant="warning" className="mb-8">{permissionError}</Alert> : null}
            {blockedByPlan ? (
              <section className="app-panel mx-auto max-w-2xl p-8">
                <div className="mb-4 flex items-center gap-3">
                  <Lock className="h-5 w-5 text-foreground/70" />
                  <h2 className="text-2xl font-display">Restricted access</h2>
                </div>
                <p className="mb-6 max-w-md text-sm text-foreground/65">
                  Your current plan does not include this feature.
                </p>
                <div>
                  <Link href="/pricing">
                    <Button size="sm">Upgrade plan</Button>
                  </Link>
                </div>
              </section>
            ) : (
              <div>{children}</div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
