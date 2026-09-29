"use client"

import * as React from "react"

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import type { HealthResponse } from "@/lib/types"

/**
 * The application shell.
 *
 * This is the dashboard-01 page structure lifted out of the page and into a
 * shared component: `SidebarProvider` → sidebar → `SidebarInset` → site header →
 * a `@container/main` content column. IncidentMind has three screens and they
 * all need the same chrome, so it lives here rather than being repeated in each
 * route. Lifting it also means the sidebar keeps its collapsed state and the
 * mobile drawer stays coherent while navigating.
 *
 * The width/height custom properties are the block's, passed to the provider so
 * the sidebar and header measure themselves against the same values.
 */
export function AppShell({
  health,
  children,
}: {
  health: HealthResponse | null
  children: React.ReactNode
}) {
  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 64)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar health={health} variant="inset" />
      <SidebarInset>
        <SiteHeader health={health} />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-3">
            <div className="flex flex-col gap-5 py-5 md:gap-8 md:py-8">
              {children}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
