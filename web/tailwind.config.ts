import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "#020617",
        foreground: "#e5e7eb",
        card: "#020617",
        cardForeground: "#e5e7eb",
        primary: {
          DEFAULT: "#22d3ee",
          foreground: "#020617"
        },
        muted: "#020617",
        border: "#1f2937"
      },
      borderRadius: {
        xl: "0.85rem",
        "2xl": "1.25rem"
      }
    }
  },
  plugins: []
};

export default config;
