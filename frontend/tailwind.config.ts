import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff8ef",
          100: "#ffefd8",
          200: "#ffd9aa",
          300: "#f8c57e",
          400: "#f2b468",
          500: "#ec9f50",
          600: "#d88236",
          700: "#b76829",
          800: "#905023",
          900: "#74411f",
          950: "#3f220f"
        },
        secondary: {
          50: "#fff2f8",
          100: "#ffd9ea",
          200: "#ffb4d4",
          300: "#f986ba",
          400: "#ea5a9f",
          500: "#cf2e79",
          600: "#ac1f64",
          700: "#8d1a53",
          800: "#721948",
          900: "#5f173d",
          950: "#390822"
        },
        accent: {
          50: "#edf6f9",
          100: "#d8eaf1",
          200: "#b5d6e3",
          300: "#84b8cd",
          400: "#5597b3",
          500: "#2a718d",
          600: "#1f5e77",
          700: "#1c4e63",
          800: "#1b414f",
          900: "#183644",
          950: "#102430"
        },
        surface: {
          50: "#f2faf6",
          100: "#e7f3ee",
          200: "#d9e9e2",
          300: "#c5dcd2",
          400: "#aac9be"
        },
        rail: {
          500: "#0f5872",
          600: "#0d4e66",
          700: "#0b4357"
        },
        success: {
          50: "#edfdf4",
          500: "#22c55e",
          700: "#15803d"
        },
        warning: {
          50: "#fffbeb",
          500: "#f59e0b",
          700: "#b45309"
        },
        danger: {
          50: "#fef2f2",
          500: "#ef4444",
          700: "#b91c1c"
        }
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "ui-sans-serif", "sans-serif"]
      },
      boxShadow: {
        soft: "0 14px 30px -18px rgba(15, 88, 114, 0.42)",
        card: "0 20px 46px -28px rgba(14, 60, 80, 0.34)",
        glow: "0 0 0 1px rgba(236, 159, 80, 0.18), 0 18px 42px -30px rgba(236, 159, 80, 0.55)"
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "float-slow": {
          "0%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
          "100%": { transform: "translateY(0px)" }
        }
      },
      animation: {
        "fade-up": "fade-up 420ms ease-out both",
        "float-slow": "float-slow 6s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

export default config;
