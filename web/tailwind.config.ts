import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "var(--ink)",
        mist: "var(--bg)",
        rule: "var(--rule)",
        mute: "var(--mute)",
        accent: "var(--accent)",
        panel: "var(--panel)",
        surface: "var(--surface)",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { opacity: "0", transform: "translateX(12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "mark-pulse": {
          "0%": { backgroundColor: "rgb(253 230 138)" },
          "100%": { backgroundColor: "rgb(254 243 199)" },
        },
      },
      animation: {
        "fade-up": "fade-up 180ms ease-out",
        "slide-in": "slide-in 200ms ease-out",
        "mark-pulse": "mark-pulse 600ms ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
