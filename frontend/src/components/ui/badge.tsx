import { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-accent-200 bg-accent-50 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-accent-700",
        className
      )}
      {...props}
    />
  );
}
