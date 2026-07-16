import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Resume Analyzer - Professional Resume Analysis & ATS Scoring",
  description: "Analyze your resume with AI-powered insights, ATS scoring, job matching, and professional suggestions to land your dream job.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
