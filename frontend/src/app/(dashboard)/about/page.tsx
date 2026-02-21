import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Our Mission</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-accent-700">
            Help people make evidence-informed food decisions with practical, accessible AI guidance.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What We Build</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-accent-700">
            A modern nutrition workspace that combines analysis, planning, recommendations, and education into one flow.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Vision</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-accent-700">
            Make nutrition intelligence scalable, personalized, and trustworthy for daily life.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
