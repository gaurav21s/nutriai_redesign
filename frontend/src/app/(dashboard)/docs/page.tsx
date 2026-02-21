import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const sections = [
  {
    title: "Platform Overview",
    content:
      "NutriAI combines food analytics, ingredient checks, meal planning, recipe generation, quizzes, and chat assistance into one authenticated dashboard.",
  },
  {
    title: "Architecture",
    content:
      "Frontend uses Next.js App Router + Clerk + Tailwind + Convex provider. Backend uses FastAPI with versioned routers, services, repositories, and typed schemas.",
  },
  {
    title: "Data Handling",
    content:
      "Convex stores per-user history for all key features. Backend writes are executed through secured Convex HTTP actions with shared-secret validation.",
  },
  {
    title: "Operational Controls",
    content:
      "Rate limits, structured logging, request IDs, typed validation, and centralized error responses are built into API middleware and dependencies.",
  },
];

export default function DocsPage() {
  return (
    <div className="space-y-4">
      {sections.map((section) => (
        <Card key={section.title}>
          <CardHeader>
            <CardTitle>{section.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-accent-700">{section.content}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
