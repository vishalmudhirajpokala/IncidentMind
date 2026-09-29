"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ActivityIcon, ArrowUpRightIcon, MenuIcon, XIcon } from "lucide-react";
import { ThemeToggle } from "@/components/common/theme-toggle";

const links = [
  { label: "Product", href: "#product-preview" },
  { label: "How it works", href: "#walkthrough" },
  { label: "Agents", href: "#agents" },
  { label: "Memory", href: "#memory" },
  { label: "Technology", href: "#technology" },
];

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 12);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <header
      className={`sticky top-0 z-50 border-b transition-[background-color,border-color,box-shadow] duration-200 ${
        scrolled
          ? "border-border/80 bg-background/95 shadow-sm backdrop-blur-md"
          : "border-transparent bg-background/80 backdrop-blur-sm"
      }`}
    >
      <nav aria-label="Main navigation" className={`mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 transition-[height] duration-200 sm:px-6 lg:px-8 ${scrolled ? "h-14" : "h-16"}`}>
        <Link href="/" className="group inline-flex min-w-0 items-center gap-2.5" onClick={closeMenu}>
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ActivityIcon aria-hidden="true" className="size-5" />
          </span>
          <span data-slot="wordmark" className="text-base text-foreground">IncidentMind</span>
        </Link>

        <div className="hidden items-center gap-7 lg:flex">
          {links.map((link) => (
            <a key={link.href} href={link.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring">
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <ThemeToggle />
          <Link href="/dashboard" className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
            Open Command Center
            <ArrowUpRightIcon aria-hidden="true" className="size-4" />
          </Link>
        </div>

        <div className="flex items-center gap-1 sm:hidden">
          <ThemeToggle />
          <button
            type="button"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            aria-controls="mobile-navigation"
            className="inline-flex size-10 items-center justify-center rounded-lg border border-border text-foreground transition-colors hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <XIcon aria-hidden="true" className="size-5" /> : <MenuIcon aria-hidden="true" className="size-5" />}
          </button>
        </div>
      </nav>

      {menuOpen ? (
        <div id="mobile-navigation" className="border-t border-border bg-background px-4 pb-4 pt-2 shadow-md sm:hidden">
          <div className="mx-auto grid max-w-7xl gap-1">
            {links.map((link) => (
              <a key={link.href} href={link.href} onClick={closeMenu} className="rounded-md px-3 py-2.5 text-sm text-foreground transition-colors hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring">
                {link.label}
              </a>
            ))}
            <Link href="/dashboard" onClick={closeMenu} className="mt-2 inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
              Open Command Center
              <ArrowUpRightIcon aria-hidden="true" className="size-4" />
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}
