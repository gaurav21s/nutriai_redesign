import { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-brand/20 bg-brand/5 px-3 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand",
        className
      )}
      {...props}
    />
  );
}
