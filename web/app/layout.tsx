import type { Metadata } from "next";
import type { ReactNode } from "react";
import { DM_Sans, Fraunces, Source_Serif_4 } from "next/font/google";

import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const sans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ResearchForge",
  description: "Source-backed equity research skeleton",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${serif.variable} ${sans.variable}`}>
      <body>{children}</body>
    </html>
  );
}
