import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";

import { cn } from "@/lib/utils";

/**
 * A determinate bar.
 *
 * Every use in this app renders the number itself as text next to the bar, so
 * the bar is a visual reinforcement of a value that is already available to a
 * screen reader. Announcing it as an unlabelled `progressbar` on top of that
 * adds a nameless widget to the accessibility tree, which is worse than not
 * exposing it at all. So: pass `label` when the bar stands on its own, and
 * otherwise the bar is hidden from assistive tech and the adjacent text
 * remains the single source of the value.
 */
export function Progress({
  className,
  value,
  label,
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root> & {
  /** Accessible name. Omit when the value is already rendered as text. */
  label?: string;
}) {
  return (
    <ProgressPrimitive.Root
      className={cn("relative h-1.5 w-full overflow-hidden rounded-full bg-muted", className)}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full w-full flex-1 bg-primary transition-transform duration-300"
        style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  );
}
