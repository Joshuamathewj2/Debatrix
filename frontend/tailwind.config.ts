import type { Config } from "tailwindcss";

export default {
  // components/ must be listed, or classes used only there are purged from the build.
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#090c12",
        panel: "#101722",
        mint: "#69f0c0",
        violet: "#a995ff",
      },
    },
  },
  plugins: [],
} satisfies Config;
