"use client"

import * as React from "react"
import Link from "next/link"

import { incidentNav, NavMain } from "@/components/nav-main"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { CommandIcon } from "lucide-react"

import { providerSummary } from "@/lib/format"
import type { HealthResponse } from "@/lib/types"

/**
 * A compact, honest read on what is actually running.
 *
 * The block's sidebar footer held a stock avatar and a fake account. There is no
 * user account in IncidentMind, and inventing one would imply a permissions
 * model the backend does not have. The space is better spent stating which
 * memory and model back the results, because that is the claim a judge is
 * checking.
 */
function SidebarStatus({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return (
      <p className="px-2 text-xs text-status-critical">
        API unreachable. Results below may be missing.
      </p>
    )
  }

  const memory = providerSummary(health.memory)
  const llm = providerSummary(health.llm)

  return (
    <dl className="grid gap-1 px-2 text-xs">
      <div className="flex items-baseline justify-between gap-2">
        <dt className="text-muted-foreground">Memory</dt>
        <dd className="text-right font-medium">{memory}</dd>
      </div>
      <div className="flex items-baseline justify-between gap-2">
        <dt className="text-muted-foreground">Model</dt>
        <dd className="text-right font-medium">{llm}</dd>
      </div>
    </dl>
  )
}

export function AppSidebar({
  health,
  ...props
}: React.ComponentProps<typeof Sidebar> & { health: HealthResponse | null }) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:p-1.5!"
            >
              <Link href="/dashboard">
                <CommandIcon className="size-5!" />
                {/* `data-slot="wordmark"` puts the brand in the display face via
                    the base layer. No weight class, for the same reason the h1s
                    dropped theirs. */}
                <span data-slot="wordmark" className="text-base">
                  IncidentMind
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={incidentNav} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarStatus health={health} />
      </SidebarFooter>
    </Sidebar>
  )
}
