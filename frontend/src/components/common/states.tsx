import { Loader2Icon, TriangleAlertIcon, InboxIcon, RefreshCwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Loading. Always a skeleton shaped like the content that is coming, so the
 * layout does not jump when data lands.
 */
export function LoadingState({
  label = "Loading",
  rows = 3,
  className,
}: {
  label?: string;
  rows?: number;
  className?: string;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={cn("space-y-2", className)}
    >
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-9 w-full" />
      ))}
    </div>
  );
}

/** Inline spinner for a button that is mid-flight. */
export function BusyLabel({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Loader2Icon className="size-4 animate-spin" />
      {children}
    </>
  );
}

/**
 * Error. Always says what happened and offers the next move. The message comes
 * from `ApiError`, which never carries a stack trace or a credential.
 */
export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-4",
        className,
      )}
    >
      <div className="flex items-start gap-2">
        <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-destructive" />
        <div className="space-y-1">
          <p className="text-sm font-medium">{title}</p>
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCwIcon />
          Try again
        </Button>
      ) : null}
    </div>
  );
}

/**
 * Empty. Says why it is empty, because "no results" and "nothing has been
 * learned yet" mean very different things to an operator.
 */
export function EmptyState({
  title,
  message,
  action,
  className,
}: {
  title: string;
  message: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 rounded-lg border border-dashed px-4 py-8 text-center",
        className,
      )}
    >
      <InboxIcon className="size-5 text-muted-foreground" />
      <p className="text-sm font-medium">{title}</p>
      <p className="max-w-md text-sm text-muted-foreground">{message}</p>
      {action}
    </div>
  );
}
