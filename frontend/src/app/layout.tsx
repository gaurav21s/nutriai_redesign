import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { AppProviders } from "@/components/providers/app-providers";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "NutriAI",
  description: "Nutrition tools for analysis, planning, and tracking.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="font-body bg-background text-foreground antialiased">
        <AppProviders>
          <div className="relative z-10 flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1 overflow-hidden">{children}</main>
            <Footer />
          </div>
        </AppProviders>
      </body>
    </html>
  );
}
