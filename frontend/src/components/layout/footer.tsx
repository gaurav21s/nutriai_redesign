import Link from "next/link";
import { Leaf } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-black/[0.08] bg-background pb-16 pt-14">
      <div className="mx-auto max-w-[1440px] px-6 sm:px-10 lg:px-16">
        <div className="mb-12 grid grid-cols-1 gap-10 md:grid-cols-12">
          <div className="md:col-span-6">
            <Link href="/" className="mb-8 flex items-center gap-3 text-foreground group">
              <div className="flex h-10 w-10 items-center justify-center bg-vibrant/10 text-vibrant">
                <Leaf className="h-6 w-6" />
              </div>
              <span className="font-display text-2xl font-bold tracking-tight">NutriAI</span>
            </Link>
            <p className="max-w-sm text-base leading-7 text-foreground/60">
              Simple tools for better nutrition choices.
            </p>
          </div>

          <div className="md:col-span-3">
            <h4 className="mb-4 text-sm text-foreground">Features</h4>
            <ul className="space-y-3 text-sm text-foreground/60">
              <li><Link href="/food-insight" className="hover:text-foreground">Food Insight</Link></li>
              <li><Link href="/meal-planner" className="hover:text-foreground">Meal Planner</Link></li>
              <li><Link href="/recipe-finder" className="hover:text-foreground">Recipe Finder</Link></li>
            </ul>
          </div>

          <div className="md:col-span-3">
            <h4 className="mb-4 text-sm text-foreground">Platform</h4>
            <ul className="space-y-3 text-sm text-foreground/60">
              <li><Link href="/about" className="hover:text-foreground">About Us</Link></li>
              <li><Link href="/articles" className="hover:text-foreground">Articles</Link></li>
              <li><Link href="/docs" className="hover:text-foreground">Docs</Link></li>
              <li><Link href="/pricing" className="hover:text-foreground">Pricing</Link></li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between border-t border-black/[0.08] pt-8 md:flex-row">
          <p className="text-xs text-foreground/45">
            © 2026 NutriAI Intelligence. All rights reserved.
          </p>
          <div className="mt-4 flex items-center gap-6 text-xs text-foreground/45 md:mt-0">
            <span>Secure connection</span>
            <span>v3</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
