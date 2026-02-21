import { TextareaHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-[120px] w-full rounded-xl border border-accent-200 bg-white/95 px-3 py-2 text-sm text-accent-900 placeholder:text-accent-400 shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200",
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
