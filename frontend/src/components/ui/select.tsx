import { SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "h-11 w-full rounded-xl border border-accent-200 bg-white/95 px-3 text-sm text-accent-900 shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200",
          className
        )}
        {...props}
      >
        {children}
      </select>
    );
  }
);

Select.displayName = "Select";
