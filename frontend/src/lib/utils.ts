/*
  The shadcn `radix-nova` components installed by `dashboard-01` merge classes
  with the `cn` package, so this module re-exports that single implementation
  rather than keeping a second clsx + tailwind-merge copy in the bundle.
*/
export { cn } from "cn";
export type { ClassValue } from "clsx";
