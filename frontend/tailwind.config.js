/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#3B82F6", light: "#60A5FA", dark: "#2563EB" },
        background: { DEFAULT: "#0F172A", card: "#1E293B", elevated: "#263548" },
        accent: { DEFAULT: "#60A5FA", light: "#93C5FD" },
        success: "#22C55E", warning: "#EAB308", danger: "#EF4444"
      },
      borderRadius: { xl: "16px", "2xl": "20px" },
      fontFamily: { sans: ["Inter", "sans-serif"] }
    }
  },
  plugins: []
}
