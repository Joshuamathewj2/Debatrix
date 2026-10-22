import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Debatrix · Think sharper",
  description: "An AI debate partner that takes the other side, cites evidence and flags fallacies.",
  icons: { icon: "/logo-mark.svg", apple: "/apple-touch-icon.png" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
