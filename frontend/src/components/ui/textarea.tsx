import { TextareaHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-[120px] w-full border-2 border-white/5 bg-white/5 px-4 py-3 text-sm font-bold uppercase tracking-widest text-white placeholder:text-neutral-600 transition-all focus:border-brand focus:bg-brand/5 focus:outline-none focus:shadow-neo-glow resize-none",
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
