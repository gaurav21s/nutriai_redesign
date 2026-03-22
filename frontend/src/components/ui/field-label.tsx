import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function FieldLabel({ children, htmlFor, className }: { children: ReactNode; htmlFor?: string; className?: string }) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn("mb-1 block text-xs font-semibold uppercase tracking-[0.12em] text-accent-600", className)}
    >
      {children}
    </label>
  );
}
