import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function ResultBlock({ title, children, className }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section className={cn("rounded-editorial border border-black/[0.03] bg-black/[0.01] p-6 mt-8", className)}>
      <h3 className="text-xs font-bold uppercase tracking-widest text-vibrant mb-6">{title}</h3>
      <div className="mt-2 text-foreground/80 leading-relaxed font-medium">{children}</div>
    </section>
  );
}
