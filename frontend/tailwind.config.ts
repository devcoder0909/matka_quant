import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0e1a",
        card: "#111827",
        primary: {
          400: "#22d3ee",
          500: "#06b6d4",
        },
        success: {
          400: "#34d399",
          500: "#10b981",
        },
        warning: {
          400: "#fbbf24",
          500: "#f59e0b",
        },
        danger: {
          400: "#fb7185",
          500: "#f43f5e",
        },
      },
    },
  },
  plugins: [],
};
export default config;
