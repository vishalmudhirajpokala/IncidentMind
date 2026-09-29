import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"
import { Slot } from "radix-ui"

const badgeVariants = cva(
  "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-4xl border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-all focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3!",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a]:hover:bg-primary/80",
        secondary:
          "bg-secondary text-secondary-foreground [a]:hover:bg-secondary/80",
        destructive:
          "bg-destructive/10 text-destructive focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:focus-visible:ring-destructive/40 [a]:hover:bg-destructive/20",
        outline:
          "border-border text-foreground [a]:hover:bg-muted [a]:hover:text-muted-foreground",
        ghost:
          "hover:bg-muted hover:text-muted-foreground dark:hover:bg-muted/50",
        link: "text-primary underline-offset-4 hover:underline",

        /*
          IncidentMind additions.

          The stock variants above are chrome, not meaning. These exist so that a
          badge whose *shade* carries meaning reads as status rather than
          decoration, and so severity is never signalled by shade alone: every
          caller also prints the severity word.

          One hue, so severity is blue *depth*: the status tokens themselves run
          dark-to-light with urgency, and the wash alpha reinforces the same
          ordering on an even ramp -- critical 20, high 17, medium 14, low 11.
          A glance down the table orders Critical above Low. Every value is
          solved against the wash rather than against the card, because the
          wash is what the text actually sits on; see `scripts/blue_contrast.py`
          for the table (worst cases 5.16-6.80:1 light, 5.16-5.49:1 dark).

          These alphas are load-bearing, not decoration. Changing one changes the
          background its text sits on, so re-run the script if you touch them.
        */
        muted: "bg-muted text-muted-foreground",
        critical: "bg-status-critical/20 text-status-critical",
        high: "bg-status-high/17 text-status-high",
        medium: "bg-status-medium/14 text-status-medium",
        low: "bg-status-low/11 text-status-low",
        ok: "bg-status-ok/17 text-status-ok",
        live: "bg-status-live/19 text-status-live",
        demo: "bg-status-demo/14 text-status-demo",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
