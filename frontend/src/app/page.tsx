"use client";

import Link from "next/link";
import Image from "next/image";
import { motion, Variants } from "framer-motion";
import {
  ArrowRight,
  Brain,
  Zap,
  Leaf,
  Microscope,
  Atom,
  Activity,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const tools = [
  {
    title: "Food Insights",
    description: "Deep neural analysis of your body's nutrient requirements and metabolic state.",
    icon: Brain,
    href: "/food-insight",
    className: "md:col-span-6 lg:col-span-8",
  },
  {
    title: "Ingredient Checker",
    description: "Analyze how different food compounds interact with your unique biochemistry.",
    icon: Microscope,
    href: "/ingredient-checker",
    className: "md:col-span-6 lg:col-span-4",
  },
  {
    title: "Meal Planner",
    description: "Algorithmic meal planning designed to optimize energy levels throughout the day.",
    icon: Leaf,
    href: "/meal-planner",
    className: "md:col-span-12 lg:col-span-6",
  },
  {
    title: "Recipe Finder",
    description: "Access curated recipes that balance molecular nutrition with culinary excellence.",
    icon: Atom,
    href: "/recipe-finder",
    className: "md:col-span-12 lg:col-span-6",
  },
];

const container: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const item: Variants = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } },
};

export default function HomePage() {
  return (
    <div className="relative bg-background">
      <div className="mx-auto w-full max-w-[1440px] px-6 sm:px-10 lg:px-16 pt-40 pb-16">
        {/* Editorial Hero */}
        <section className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-32">
          <div className="md:col-span-7 flex flex-col justify-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="mb-6 flex items-center gap-3 text-vibrant font-semibold tracking-widest uppercase text-[10px]"
            >
              <div className="h-[1px] w-12 bg-vibrant/30" />
              NutriAI — High Precision Nutrition
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.2, ease: [0.19, 1, 0.22, 1] }}
              className="text-7xl sm:text-8xl lg:text-9xl font-display mb-10 leading-[0.9] text-foreground"
            >
              Fuel <span className="italic text-vibrant">your</span> <br />
              Potential.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1.2, delay: 0.4 }}
              className="text-foreground/70 text-xl mb-12 max-w-xl leading-relaxed"
            >
              Experience the pinnacle of nutrition technology. Our AI platform crafts a personalized narrative
              for your health, focused on data-driven insights and biological harmony.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-wrap gap-6"
            >
              <Link href="/food-insight">
                <Button size="lg" className="rounded-full px-10 bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow group">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
              <Link href="/docs">
                <Button variant="outline" size="lg" className="rounded-full px-10 border-foreground/10 hover:bg-foreground/5 text-foreground">
                  View Documentation
                </Button>
              </Link>
            </motion.div>
          </div>

          <div className="md:col-span-5 relative mt-16 md:mt-0">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.5, ease: [0.19, 1, 0.22, 1] }}
              className="aspect-[4/5] rounded-editorial overflow-hidden shadow-elegant border border-black/[0.03] relative"
            >
              <Image
                src="/images/hero_food_1.png"
                alt="High-end culinary nutrition"
                fill
                priority
                className="object-cover transition-transform duration-[3s] hover:scale-105"
                sizes="(max-width: 768px) 100vw, 40vw"
              />
            </motion.div>
            <div className="absolute -bottom-8 -left-8 p-10 editorial-card max-w-[260px] hidden lg:block border border-black/5 shadow-elegant">
              <p className="font-display text-2xl mb-4 italic leading-tight">"Where data meets culinary artistry."</p>
              <p className="text-[10px] font-bold uppercase tracking-widest text-vibrant">Elite Status</p>
            </div>
          </div>
        </section>

        {/* Highlight Section */}
        <section className="mb-48 text-center max-w-4xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="text-5xl font-display mb-16 text-foreground"
          >
            Built for <span className="vibrant-highlight font-display">Performance.</span>
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-16">
            <div className="group">
              <p className="text-4xl font-display italic text-vibrant mb-6 transition-transform group-hover:scale-110">01.</p>
              <h3 className="text-xs font-bold uppercase tracking-widest mb-4 text-foreground">Precision</h3>
              <p className="text-sm text-foreground/50 leading-relaxed font-medium">Molecular analysis of every nutrient for your specific biological needs.</p>
            </div>
            <div className="group">
              <p className="text-4xl font-display italic text-vibrant mb-6 transition-transform group-hover:scale-110">02.</p>
              <h3 className="text-xs font-bold uppercase tracking-widest mb-4 text-foreground">Clarity</h3>
              <p className="text-sm text-foreground/50 leading-relaxed font-medium">No more guesswork. Get clear, actionable insights in seconds.</p>
            </div>
            <div className="group">
              <p className="text-4xl font-display italic text-vibrant mb-6 transition-transform group-hover:scale-110">03.</p>
              <h3 className="text-xs font-bold uppercase tracking-widest mb-4 text-foreground">Control</h3>
              <p className="text-sm text-foreground/50 leading-relaxed font-medium">Complete visibility over your nutritional journey and outcomes.</p>
            </div>
          </div>
        </section>

        {/* Feature Grid */}
        <section>
          <div className="mb-20 flex flex-col md:flex-row md:items-end justify-between gap-8 border-b border-black/[0.03] pb-12">
            <h2 className="text-6xl font-display max-w-xl text-foreground">
              Powerful <br />
              <span className="text-vibrant italic font-display underline decoration-vibrant/20 underline-offset-8">Intelligence.</span>
            </h2>
            <p className="text-foreground/60 max-w-sm mb-2 text-lg leading-relaxed">
              Our suite of professional tools designed for high-performance living.
            </p>
          </div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
            className="grid grid-cols-12 gap-8"
          >
            {tools.map((tool) => {
              const Icon = tool.icon;
              return (
                <motion.div
                  key={tool.title}
                  variants={item}
                  className={tool.className}
                >
                  <Link href={tool.href} className="block h-full transition-all duration-500 hover:-translate-y-2 group">
                    <Card className="h-full border border-black/[0.03] shadow-soft-glow bg-white/60 backdrop-blur-sm p-4 hover:border-vibrant/20 transition-colors">
                      <CardHeader className="p-8">
                        <div className="mb-10 flex h-16 w-16 items-center justify-center rounded-2xl bg-vibrant/5 text-vibrant ring-1 ring-vibrant/10 group-hover:bg-vibrant group-hover:text-white transition-all duration-500">
                          <Icon className="h-7 w-7" />
                        </div>
                        <CardTitle className="text-4xl mb-6 font-display group-hover:text-vibrant transition-colors">{tool.title}</CardTitle>
                        <CardDescription className="text-lg text-foreground/50 leading-relaxed font-medium">
                          {tool.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="px-8 pb-8 flex justify-end">
                        <div className="h-12 w-12 flex items-center justify-center rounded-full border border-black/5 group-hover:bg-vibrant group-hover:text-white group-hover:border-vibrant transition-all duration-500">
                          <ArrowRight className="h-5 w-5" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </motion.div>
        </section>

        {/* Secondary Visual Section */}
        <section className="mt-32 grid grid-cols-1 md:grid-cols-12 gap-16 items-center">
          <div className="md:col-span-6 relative order-2 md:order-1">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 1.2 }}
              className="aspect-square md:aspect-[16/10] rounded-editorial overflow-hidden shadow-elegant border border-black/[0.03] relative"
            >
              <Image
                src="/images/hero_food_2.png"
                alt="Serene health smoothie"
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 50vw"
              />
            </motion.div>
            <div className="absolute -top-6 -right-6 p-8 bg-vibrant rounded-full text-white shadow-soft-glow animate-pulse hidden md:block z-20">
              <Sparkles className="h-8 w-8" />
            </div>
          </div>
          <div className="md:col-span-6 order-1 md:order-2">
            <h2 className="text-6xl font-display mb-8 text-foreground leading-[1]"><span className="text-vibrant italic font-display">Refine</span> Your <br /> Strategy.</h2>
            <p className="text-foreground/60 mb-12 text-xl leading-relaxed">
              We translate complex biomarkers into clear, actionable, and visually stunning nutrition plans. Data has never looked this good.
            </p>
            <Button size="lg" className="rounded-full px-12 bg-foreground text-background hover:bg-foreground/90 transition-all font-semibold">Join the Elite</Button>
          </div>
        </section>
      </div>

    </div>
  );
}
