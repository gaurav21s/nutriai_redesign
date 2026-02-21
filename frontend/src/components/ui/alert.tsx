import { ReactNode } from "react";

import { cn } from "@/lib/cn";

type AlertVariant = "info" | "success" | "warning" | "error";

const variantClass: Record<AlertVariant, string> = {
  info: "border-accent-200 bg-accent-50/85 text-accent-700",
  success: "border-success-500/30 bg-success-50 text-success-700",
  warning: "border-warning-500/30 bg-warning-50 text-warning-700",
  error: "border-danger-500/30 bg-danger-50 text-danger-700",
};

export function Alert({ variant = "info", children }: { variant?: AlertVariant; children: ReactNode }) {
  return <div className={cn("rounded-2xl border px-4 py-3 text-sm shadow-sm", variantClass[variant])}>{children}</div>;
}
