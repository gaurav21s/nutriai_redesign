"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Apple,
  Brain,
  Calculator,
  FolderKanban,
  LayoutGrid,
  Leaf,
  Lock,
  MessageSquare,
  Microscope,
  ShieldCheck,
  Soup,
  Sparkles,
} from "lucide-react";

import { cn } from "@/lib/cn";

type PermissionMap = Record<string, boolean>;

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutGrid;
  permissionKey?: string;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const sections: NavSection[] = [
  {
    title: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutGrid }],
  },
  {
    title: "Tools",
    items: [
      { href: "/food-insight", label: "Food Insight", icon: Brain, permissionKey: "food_insight" },
      { href: "/ingredient-checker", label: "Ingredient Checker", icon: Microscope, permissionKey: "ingredient_checker" },
      { href: "/meal-planner", label: "Meal Planner", icon: Leaf, permissionKey: "meal_planner" },
      { href: "/recipe-finder", label: "Recipe Finder", icon: Soup, permissionKey: "recipe_finder" },
      { href: "/nutri-chat", label: "Nutri Chat", icon: MessageSquare, permissionKey: "nutri_chat" },
      { href: "/nutri-quiz", label: "Nutri Quiz", icon: Sparkles, permissionKey: "nutri_quiz" },
      { href: "/nutri-calc", label: "Nutri Calc", icon: Calculator, permissionKey: "nutri_calc" },
      { href: "/recommendations", label: "Recommendations", icon: Apple, permissionKey: "recommendations" },
    ],
  },
  {
    title: "Account",
    items: [
      { href: "/library", label: "Library", icon: FolderKanban },
      { href: "/subscription", label: "Subscription", icon: ShieldCheck },
    ],
  },
];

export function Sidebar({
  onNavigate,
  permissions,
  collapsed = false,
}: {
  onNavigate?: () => void;
  permissions?: PermissionMap | null;
  collapsed?: boolean;
}) {
  const pathname = usePathname();

  return (
    <aside className="flex h-full flex-col border-r border-black/[0.08] bg-white">
      <div className={cn("border-b border-black/[0.08] py-4", collapsed ? "px-3" : "px-4")}>
        <Link
          href="/dashboard"
          onClick={onNavigate}
          className={cn("flex items-center", collapsed ? "justify-center" : "gap-3")}
          title="Dashboard"
        >
          <div className="relative h-8 w-8 flex-shrink-0">
            <Image
              src="/images/nutriai-favicon-color.png"
              alt="NutriAI"
              fill
              className="object-contain"
            />
          </div>
          {!collapsed ? (
            <div>
              <div className="text-sm font-semibold text-vibrant">NutriAI</div>
              <div className="text-xs text-foreground/55">Dashboard</div>
            </div>
          ) : null}
        </Link>
      </div>

      <nav className={cn("flex-1 overflow-y-auto py-4", collapsed ? "px-2" : "px-3")}>
        <div className="space-y-6">
          {sections.map((section) => (
            <div key={section.title}>
              {!collapsed ? (
                <div className="px-3 pb-2 text-xs text-foreground/55">{section.title}</div>
              ) : null}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                  const locked = Boolean(item.permissionKey && permissions && permissions[item.permissionKey] === false);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={locked ? "/pricing" : item.href}
                      onClick={onNavigate}
                      title={item.label}
                      className={cn(
                        "flex items-center py-2 text-sm",
                        collapsed ? "justify-center px-2" : "gap-3 px-3",
                        active ? "bg-muted text-foreground" : "text-foreground/70 hover:bg-muted hover:text-foreground",
                        locked && "opacity-70"
                      )}
                    >
                      <Icon className={cn("h-4 w-4 flex-shrink-0 text-vibrant", active && "text-vibrant")} />
                      {!collapsed ? <span className="flex-1">{item.label}</span> : null}
                      {!collapsed && locked ? <Lock className="h-3.5 w-3.5 text-foreground/40" /> : null}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>
    </aside>
  );
}
