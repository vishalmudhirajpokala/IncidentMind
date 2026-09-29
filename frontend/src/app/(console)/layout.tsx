import { AppShell } from "@/components/app-shell"
import { api } from "@/lib/api-server"
import type { HealthResponse } from "@/lib/types"

/*
  The console layout: the dashboard-01 shell, shared by all three screens.

  `/health` is fetched here, once, and handed to both the sidebar and the header.
  It is the same call the pages make, so the chrome and the content can never
  disagree about whether memory and the model are live. If the API is down this
  resolves to `null` rather than throwing, which lets the shell keep rendering
  and say so, instead of blanking every screen.
*/
export const dynamic = "force-dynamic";

export default async function ConsoleLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const health: HealthResponse | null = await api.health().catch(() => null);

  return <AppShell health={health}>{children}</AppShell>;
}
