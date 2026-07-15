/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Fraunces"', "serif"],
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
        script: ['"Caveat"', "cursive"],
      },
      colors: {
        // Brand palette
        cream: "#F7F3EA",
        paper: "#FBF7EE",
        ink: "#0B2E2A",
        teal: {
          DEFAULT: "#0F4C5C",
          deep: "#083D38",
          soft: "#1F6A6E",
        },
        mustard: {
          DEFAULT: "#E9A24B",
          soft: "#F1C57C",
          deep: "#C6852E",
        },
        leaf: "#4CAF50",
        // shadcn tokens
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        paper: "6px 6px 0 rgba(11,46,42,0.12)",
        "paper-sm": "3px 3px 0 rgba(11,46,42,0.10)",
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' }
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' }
        },
        floaty: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        pulseRing: {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        coinFlip: {
          "0%": { transform: "rotateY(0deg)" },
          "45%,55%": { transform: "rotateY(180deg)" },
          "100%": { transform: "rotateY(360deg)" },
        },
        coinSpin: {
          "0%": { transform: "rotateY(0deg)" },
          "100%": { transform: "rotateY(360deg)" },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        floaty: 'floaty 6s ease-in-out infinite',
        pulseRing: 'pulseRing 1.8s ease-out infinite',
        coinFlip: 'coinFlip 1.6s cubic-bezier(0.6,0.05,0.28,0.91)',
        coinFlipLoop: 'coinFlip 6s ease-in-out infinite',
        coinSpin: 'coinSpin 1.2s ease-in-out',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
