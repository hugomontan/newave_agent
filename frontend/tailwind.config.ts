import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // BTG Pactual - Elegant Corporate Palette
        btg: {
          navy: "#0d2847",        // Deep navy (primary) - sophisticated, trustworthy
          navyLight: "#1a3d66",   // Slightly lighter navy for hover states
          navyDark: "#0a1f38",    // Darker navy for pressed states
          navyUltraLight: "#e8ecf2", // Ultra light navy for backgrounds
          navyVeryLight: "#d4dce8",  // Very light navy for subtle backgrounds
          gold: "#e6b800",        // Elegant gold (use sparingly for premium highlights)
          goldLight: "#f5c842",   // Lighter gold variant
          goldDark: "#c99f00",    // Darker gold variant
          graphite: {
            50: "#f3f5f7",        // Very light gray-blue
            100: "#e8ecef",       // Light gray-blue
            200: "#d1d7dc",       // Light gray
            300: "#b8c2ca",       // Medium-light
            400: "#9ca3af",       // Medium
            500: "#6b7280",       // Medium-dark
            600: "#4b5563",       // Dark
            700: "#374151",       // Darker
            800: "#1f2937",       // Very dark
            900: "#111827",       // Almost black
          },
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
