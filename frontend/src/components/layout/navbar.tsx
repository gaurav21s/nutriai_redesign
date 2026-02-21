import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";
import { Compass, Leaf, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-accent-700/15 bg-white/82 backdrop-blur-lg">
      <div className="mx-auto flex h-16 w-full max-w-[1480px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="inline-flex items-center gap-2 text-accent-800">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand-200 text-secondary-700">
            <Leaf className="h-4 w-4" />
          </span>
          <span className="font-display text-2xl leading-none">NutriAI</span>
        </Link>

        <nav className="hidden items-center gap-7 text-sm font-semibold text-accent-700 md:flex">
          <Link href="/" className="transition-colors hover:text-accent-900">
            Home
          </Link>
          <Link href="/food-insight" className="transition-colors hover:text-accent-900">
            Dashboard
          </Link>
          <Link href="/docs" className="transition-colors hover:text-accent-900">
            Docs
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          <SignedOut>
            <SignInButton mode="modal">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </SignInButton>
            <SignUpButton mode="modal">
              <Button size="sm" className="gap-1.5">
                Start
                <Sparkles className="h-3.5 w-3.5" />
              </Button>
            </SignUpButton>
          </SignedOut>

          <SignedIn>
            <Link href="/food-insight">
              <Button variant="secondary" size="sm" className="hidden sm:inline-flex gap-1.5">
                <Compass className="h-3.5 w-3.5" />
                Dashboard
              </Button>
            </Link>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
        </div>
      </div>
    </header>
  );
}
