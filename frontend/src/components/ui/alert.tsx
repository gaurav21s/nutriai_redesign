import { ReactNode } from "react";
import { cn } from "@/lib/cn";

type AlertVariant = "info" | "success" | "warning" | "error";

const variantClass: Record<AlertVariant, string> = {
  info: "border-black/[0.05] bg-white text-foreground/60",
  success: "border-brand/30 bg-brand/5 text-brand",
  warning: "border-ochre/30 bg-ochre/5 text-ochre",
  error: "border-red-200 bg-red-50 text-red-600",
};

export function Alert({
  variant = "info",
  children,
  className
}: {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-editorial border px-6 py-4 text-sm font-medium leading-relaxed", variantClass[variant], className)}>
      {children}
    </div>
  );
}
