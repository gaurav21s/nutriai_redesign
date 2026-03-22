const sections = [
  {
    title: "What the platform does",
    content:
      "NutriAI covers food analysis, ingredient checks, meal plans, recipes, chat, quizzes, and nutrition calculations.",
  },
  {
    title: "How the product is built",
    content:
      "The frontend uses Next.js. The backend uses FastAPI. Saved records and supporting data are stored through Convex.",
  },
  {
    title: "Authentication and access",
    content:
      "Clerk handles sign in. Public pages stay open, while dashboard tools use sign-in state and plan permissions.",
  },
  {
    title: "API behavior",
    content:
      "Feature requests go through typed API clients, backend validation, and structured JSON responses.",
  },
];

export default function DocsPage() {
  return (
    <div className="bg-background pt-40 pb-20">
      <div className="mx-auto w-full max-w-[1280px] px-6 sm:px-10 lg:px-16">
        <div className="space-y-10">
          <header className="border-b border-black/[0.08] pb-8">
            <h1 className="text-6xl sm:text-7xl font-display leading-[0.95] text-foreground">
              Product <span className="italic text-vibrant">Docs</span>
            </h1>
            <p className="mt-6 max-w-2xl text-xl leading-relaxed text-foreground/60">
              Product notes, architecture basics, and platform behavior in one place.
            </p>
          </header>

          <div className="grid gap-4">
            {sections.map((section) => (
              <section key={section.title} className="app-panel p-8">
                <h2 className="text-3xl font-display text-foreground">{section.title}</h2>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-foreground/70">{section.content}</p>
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
