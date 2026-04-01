"use client";

import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";
import Image from "next/image";

import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <div className="fixed left-0 right-0 top-0 z-[100] border-b border-black/[0.08] bg-background">
      <header className="mx-auto flex h-16 w-full max-w-[1560px] items-center justify-between px-8 sm:px-10 lg:px-14">
        <Link href="/" className="inline-flex items-center gap-3 text-foreground">
          <div className="relative h-10 w-10 flex-shrink-0">
            <Image
              src="/images/nutriai-favicon-color.png"
              alt="NutriAI"
              fill
              className="object-contain"
              priority
            />
          </div>
          <div className="leading-none">
            <div className="text-[28px] font-display font-semibold tracking-tight text-foreground">
              <span>Nutri</span>
              <span className="text-vibrant italic">AI</span>
            </div>
            <div className="mt-1 text-[11px] text-foreground/55">
              Your Nutrition Companion
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-foreground/75 md:flex">
          <Link href="/about" className="hover:text-foreground">
            About Us
          </Link>
          <Link href="/articles" className="hover:text-foreground">
            Articles
          </Link>
          <Link href="/docs" className="hover:text-foreground">
            Docs
          </Link>
          <Link href="/pricing" className="hover:text-foreground">
            Pricing
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          <SignedOut>
            <SignInButton mode="modal">
              <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
                Sign in
              </Button>
            </SignInButton>
            <SignUpButton mode="modal">
              <Button size="sm" variant="primary">
                Get started
              </Button>
            </SignUpButton>
          </SignedOut>

          <SignedIn>
            <Link href="/dashboard">
              <Button variant="outline" size="sm" className="px-4">
                Dashboard
              </Button>
            </Link>
            <UserButton appearance={{ elements: { userButtonAvatarBox: "h-8 w-8 rounded-full border border-black/10" } }} afterSignOutUrl="/" />
          </SignedIn>
        </div>
      </header>
    </div>
  );
}
