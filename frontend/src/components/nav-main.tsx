"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import {
  HistoryIcon,
  LayoutDashboardIcon,
  SirenIcon,
} from "lucide-react"

export type NavItem = {
  title: string
  url: string
  icon?: React.ReactNode
  /** Longer name used in the collapsed tooltip and for screen readers. */
  description?: string
}

export function NavMain({ items }: { items: NavItem[] }) {
  const pathname = usePathname()

  /*
    The incident list lives on the command center, so "Incidents" targets that
    table via its anchor rather than inventing a fourth screen. Highlighting is
    therefore decided by route: the table is current while the command center
    root is, and a specific incident is current once one is open.
  */
  const [hash, setHash] = React.useState("")

  React.useEffect(() => {
    const read = () => setHash(window.location.hash)
    read()
    window.addEventListener("hashchange", read)
    return () => window.removeEventListener("hashchange", read)
  }, [pathname])

  function isActive(item: NavItem) {
    if (item.url.startsWith("#") || item.url.includes("#")) {
      const anchor = item.url.slice(item.url.indexOf("#"))
      return pathname === "/dashboard" && hash === anchor
    }
    if (item.url === "/dashboard") {
      return pathname === "/dashboard" && hash !== "#incidents"
    }
    if (item.url === "/history") return pathname === "/history"
    return pathname.startsWith(item.url)
  }

  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const active = isActive(item)
            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  asChild
                  isActive={active}
                  tooltip={item.description ?? item.title}
                  aria-current={active ? "page" : undefined}
                  className={active ? "data-[active=true]:bg-primary data-[active=true]:text-primary-foreground" : undefined}
                >
                  <Link href={item.url}>
                    {item.icon}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

export const incidentNav: NavItem[] = [
  {
    title: "Command Center",
    url: "/dashboard",
    icon: <LayoutDashboardIcon />,
    description: "Active incidents and recent learning",
  },
  {
    title: "Incidents",
    url: "/dashboard#incidents",
    icon: <SirenIcon />,
    description: "Every incident currently on record",
  },
  {
    title: "History",
    url: "/history",
    icon: <HistoryIcon />,
    description: "Retained experiences and resolved incidents",
  },
]
