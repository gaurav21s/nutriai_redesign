import { InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-11 w-full rounded-xl border border-accent-200 bg-white/95 px-3 text-sm text-accent-900 placeholder:text-accent-400 shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
