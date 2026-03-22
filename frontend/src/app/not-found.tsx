import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center animate-reveal">
            <div className="mb-12 inline-flex h-24 w-24 items-center justify-center rounded-full bg-vibrant/5 text-vibrant shadow-soft-glow ring-1 ring-vibrant/10">
                <Search className="h-10 w-10" />
            </div>
            <h1 className="text-7xl font-display mb-6 tracking-tighter">404 <span className="text-vibrant italic">—</span> Baseline Lost.</h1>
            <p className="max-w-md text-lg font-medium text-foreground/50 italic leading-relaxed mb-12">
                The biological protocol you are attempting to access does not exist in our current synthesis.
            </p>
            <div className="flex flex-wrap justify-center gap-6">
                <Link href="/">
                    <Button size="lg" className="rounded-full px-12 bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow">
                        Initialize Baseline
                    </Button>
                </Link>
                <Link href="/food-insight">
                    <Button variant="outline" size="lg" className="rounded-full px-12 border-black/5 hover:bg-black/5">
                        Dashboard
                    </Button>
                </Link>
            </div>
        </div>
    );
}
