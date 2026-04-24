import { redirect } from "next/navigation";

export default async function RecommendationsRedirectPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const params = new URLSearchParams();
  const query = typeof resolvedSearchParams?.query === "string" ? resolvedSearchParams.query : "";
  const type = typeof resolvedSearchParams?.type === "string" ? resolvedSearchParams.type : "";

  params.set("mode", type === "healthier_alternative" ? "compare_options" : "situation_pick");
  params.set("goal", "healthy_lifestyle");
  if (query) {
    params.set("context", query);
    params.set("situation", query);
  }

  redirect(`/nutri-smart-picks?${params.toString()}`);
}
