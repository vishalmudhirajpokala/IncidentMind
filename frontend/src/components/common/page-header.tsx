import { cn } from "@/lib/utils";

/**
 * The per-route page heading.
 *
 * The shadcn site header used to own the page's `h1`; in IncidentMind it owns
 * only the brand and the provider readout, so each route declares its own single
 * top-level heading here. That keeps one `h1` per document, which is what lets
 * the incident page use the incident's own title as its heading.
 */
export function PageHeader({
  title,
  subtitle,
  actions,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("flex flex-wrap items-end justify-between gap-4", className)}
    >
      <div className="space-y-2">
        {/*
          No `font-semibold`. The base layer puts every `h1` in the display face,
          which ships a single weight, and a 600 request would let the browser
          embolden the CFF outline synthetically. `tracking-tight` is kept --
          unlike the body correction, a small negative tracking is right for an
          18px display heading.
        */}
        <h1 className="text-lg tracking-tight">{title}</h1>
        {subtitle ? (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex flex-wrap items-center gap-2">{actions}</div>
      ) : null}
    </div>
  );
}
