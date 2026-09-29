import type { Metadata } from "next";
import { DM_Sans, Roboto_Mono } from "next/font/google";
import { themeBootstrapScript } from "@/components/common/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-roboto-mono",
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "IncidentMind — Memory-First AI Incident Response",
  description:
    "AI agents investigate production incidents using persistent organizational memory, historical experience, and evidence-backed recommendations.",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "IncidentMind",
    title: "IncidentMind — Memory-First AI Incident Response",
    description:
      "AI agents investigate production incidents using persistent organizational memory, historical experience, and evidence-backed recommendations.",
  },
  twitter: {
    card: "summary",
    title: "IncidentMind — Memory-First AI Incident Response",
    description:
      "AI agents investigate production incidents using persistent organizational memory, historical experience, and evidence-backed recommendations.",
  },
};

/**
 * Root layout.
 *
 * Static chrome only. Data is fetched by the pages so that a backend outage
 * degrades one screen rather than the whole application, and so the header
 * badges and the page content can never disagree about provider mode.
 */
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // `suppressHydrationWarning` is required: the pre-paint script below adds
    // the `dark` class to this element, so the server and client markup
    // necessarily differ.
    <html
      lang="en"
      className={`${dmSans.variable} ${robotoMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrapScript }} />
      </head>
      <body className="min-h-screen font-sans">
        <TooltipProvider delayDuration={200}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
