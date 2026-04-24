import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-editorial border border-black/[0.12] bg-white px-3 text-sm text-foreground ring-offset-background placeholder:text-foreground/35 transition-colors duration-150 focus:border-heritage/25 focus:outline-none focus:ring-2 focus:ring-heritage/10",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
