import { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/cn";

interface FeatureShellProps {
  title: string;
  description: string;
  children: ReactNode;
  aside?: ReactNode;
  className?: string;
}

export function FeatureShell({ title, description, children, aside, className }: FeatureShellProps) {
  return (
    <div className={cn("grid gap-7 xl:grid-cols-[1.7fr_1fr]", className)}>
      <Card className="animate-fade-up border-accent-200/70 bg-white/90">
        <CardHeader className="pb-3">
          <CardTitle className="text-[2rem] sm:text-[2.2rem]">{title}</CardTitle>
          <p className="mt-1 max-w-3xl text-sm text-accent-600">{description}</p>
        </CardHeader>
        <CardContent className="pt-1">{children}</CardContent>
      </Card>

      <div className="space-y-7">{aside}</div>
    </div>
  );
}
