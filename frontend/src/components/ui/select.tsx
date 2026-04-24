import { SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "h-10 w-full rounded-editorial border border-black/[0.12] bg-white px-3 text-sm text-foreground focus:border-heritage/25 focus:outline-none focus:ring-2 focus:ring-heritage/10",
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
