import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Sidebar / superficies oscuras (navy profundo de la referencia).
        ink: {
          950: "#0a1626",
          900: "#0e1c30",
          800: "#152741",
          700: "#1d3553",
          600: "#274566",
        },
        // Acento principal (teal/esmeralda).
        accent: {
          50: "#ecfdf7",
          100: "#d1faec",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
        // Lienzo de contenido.
        canvas: "#f5f7fa",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 24 40 / 0.04), 0 1px 3px 0 rgb(16 24 40 / 0.06)",
        cardhover: "0 4px 12px -2px rgb(16 24 40 / 0.10)",
      },
      borderRadius: {
        xl: "0.85rem",
      },
    },
  },
  plugins: [],
};

export default config;
