import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#faf8f5",
        foreground: "#292524",
        card: {
          DEFAULT: "#ffffff",
          foreground: "#292524",
        },
        brand: {
          DEFAULT: "#b45309",
          foreground: "#FFFFFF",
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
          950: "#431407",
        },
        vibrant: {
          DEFAULT: "#d97706",
          foreground: "#FFFFFF",
        },
        ochre: {
          DEFAULT: "#f3e7d3",
          foreground: "#292524",
        },
        muted: {
          DEFAULT: "#f5f5f4",
          foreground: "#57534e",
        },
        accent: {
          DEFAULT: "#d97706",
          foreground: "#FFFFFF",
        },
      },
      fontFamily: {
        display: ["IBM Plex Sans", "Aptos", "Helvetica Neue", "sans-serif"],
        body: ["IBM Plex Sans", "Aptos", "Helvetica Neue", "sans-serif"],
      },
      boxShadow: {
        "soft-glow": "0 2px 8px rgba(0, 0, 0, 0.08)",
        "elegant": "0 2px 8px rgba(0, 0, 0, 0.08)",
      },
      borderRadius: {
        "editorial": "10px",
      },
    },
  },
  plugins: [],
};

export default config;
