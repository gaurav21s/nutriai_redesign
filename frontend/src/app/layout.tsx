import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Fraunces, Manrope } from "next/font/google";
import type { ReactNode } from "react";

import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { ConvexClientProvider } from "@/lib/convex";
import "@/styles/globals.css";

const displayFont = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

const bodyFont = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "NutriAI",
  description: "AI-powered nutrition companion",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${displayFont.variable} ${bodyFont.variable} font-body`}>
          <ConvexClientProvider>
            <Navbar />
            <main className="min-h-[calc(100vh-8rem)]">{children}</main>
            <Footer />
          </ConvexClientProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
