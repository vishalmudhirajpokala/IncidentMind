import { ThemeToggle } from "@/components/common/theme-toggle"
import { DemoModeBadge, ModeSummary, ProviderIndicators } from "@/components/common/mode-badges"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import type { HealthResponse } from "@/lib/types"

/**
 * The site header, adapted from the dashboard-01 block.
 *
 * Height, trigger, separator and the collapsible-height behaviour are the
 * block's. The brand and the provider readout are IncidentMind's, and they read
 * from the same `/health` payload the page uses, so the header can never claim
 * a mode the content disagrees with.
 *
 * There is deliberately no `h1` here. Each route renders exactly one top-level
 * heading for its own content (the incident title, for instance), and a second
 * `h1` in the chrome would break the document outline.
 */
export function SiteHeader({ health }: { health: HealthResponse | null }) {
  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />
        <div className="flex min-w-0 flex-col leading-none">
          {/* Brand in the display face, tagline in the text face -- see the
              base-layer rule in globals.css. The tagline stays in the sans stack
              to keep the header compact and readable next to the display wordmark. */}
          <span data-slot="wordmark" className="truncate text-sm">
            IncidentMind
          </span>
          <span className="truncate text-[11px] text-muted-foreground">
            Memory-first incident response
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="hidden cursor-default md:inline-flex">
                <ProviderIndicators health={health} />
              </span>
            </TooltipTrigger>
            <TooltipContent>{ModeSummary({ health })}</TooltipContent>
          </Tooltip>
          <DemoModeBadge demoMode={health?.demo_mode ?? false} />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
