/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
          hover: "var(--primary-hover)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
          soft: "var(--accent-soft)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        // LungCancer.NET Clinical Tokens (Node 3:3)
        clinical: {
          blue: "#1E3A8A",
          "blue-hover": "#1E40AF",
          teal: "#0D9488",
          "teal-soft": "#14B8A6",
          ruleout: {
            DEFAULT: "var(--tier-ruleout)",
            bg: "var(--tier-ruleout-bg)",
            border: "var(--tier-ruleout-border)",
          },
          review: {
            DEFAULT: "var(--tier-review)",
            bg: "var(--tier-review-bg)",
            border: "var(--tier-review-border)",
          },
          refer: {
            DEFAULT: "var(--tier-refer)",
            bg: "var(--tier-refer-bg)",
            border: "var(--tier-refer-border)",
          },
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
        chart: {
          1: "var(--chart-1)",
          2: "var(--chart-2)",
          3: "var(--chart-3)",
          4: "var(--chart-4)",
          5: "var(--chart-5)",
        },
      },
      fontFamily: {
        sans: ["Inter", "Source Sans 3", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        // Typography scale from Node 3:3
        "micro": ["13px", { lineHeight: "16px", letterSpacing: "0.08em", fontWeight: "500" }],
        "caption": ["15px", { lineHeight: "20px", fontWeight: "400" }],
        "body": ["18px", { lineHeight: "1.6", fontWeight: "400" }],
        "h3": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "h2": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "h1": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "clinical-val": ["40px", { lineHeight: "48px", fontWeight: "700" }],
      },
      spacing: {
        // 8px base grid
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "6": "24px",
        "8": "32px",
        "12": "48px",
        "16": "64px",
        "card-pad": "24px",
        "section-gap": "32px",
        "form-gap": "16px",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 4px)",
        sm: "calc(var(--radius) - 6px)",
        card: "12px",
        button: "8px",
        input: "8px",
        tier: "9999px",
      },
      boxShadow: {
        "elevation-1": "var(--elevation-1)",
        "elevation-2": "var(--elevation-2)",
      },
    },
  },
  plugins: [],
};
