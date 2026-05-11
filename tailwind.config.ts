import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "nb-navy": "#0a1628",
        "nb-gold": "#c9a84c",
        "nb-slate": "#1e293b",
      },
    },
  },
  plugins: [],
};

export default config;
