import { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ResultBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="border-brand-200/75 bg-white/95">
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
