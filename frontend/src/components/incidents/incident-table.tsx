"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowUpDownIcon, ArrowUpIcon, ArrowDownIcon, Columns3Icon } from "lucide-react";

import { EmptyState } from "@/components/common/states";
import { SeverityBadge, StatusBadge } from "@/components/incidents/badges";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDuration, formatRelative, incidentTimestamp, SEVERITY_RANK } from "@/lib/format";
import type { Incident } from "@/lib/types";
import { cn } from "@/lib/utils";

type SortKey = "severity" | "started" | "status" | "resolution";
type ColumnId = "id" | "title" | "service" | "severity" | "status" | "started" | "root_cause" | "resolution";

/*
  `hideBelow` is a responsive default, not a hard rule: a column the layout drops
  at a given width is still listed in the Columns menu, and choosing it there
  suppresses the responsive class so an operator on a narrow screen can always
  bring a column back.

  All eight columns need roughly 1250px to sit side by side, and the sidebar takes
  a fixed 256px, so the two widest text columns are held back until there is
  genuinely room for them: service from `xl`, root cause from `2xl`. `Started`
  goes on phones only — it is the widest of the remaining cells and the least
  useful for triage, since the incident page always shows the exact time.
*/
const COLUMNS: {
  key: ColumnId;
  label: string;
  className?: string;
  hideBelow?: "sm" | "xl" | "2xl";
}[] = [
  { key: "id", label: "ID", className: "w-20" },
  { key: "title", label: "Incident" },
  { key: "service", label: "Service", hideBelow: "xl" },
  { key: "severity", label: "Severity" },
  { key: "status", label: "Status" },
  { key: "started", label: "Started", hideBelow: "sm" },
  { key: "root_cause", label: "Root cause", hideBelow: "2xl", className: "max-w-[16rem]" },
  { key: "resolution", label: "Resolution", className: "text-right" },
];

/*
  Tailwind only sees class names that appear literally in the source, so these
  are written out in full rather than assembled from the breakpoint name.
  Interpolating `` `hidden ${bp}:table-cell` `` compiles cleanly and then
  silently does nothing, because no such utility is ever generated.
*/
const RESPONSIVE_HIDE: Record<
  NonNullable<(typeof COLUMNS)[number]["hideBelow"]>,
  string
> = {
  sm: "hidden sm:table-cell",
  xl: "hidden xl:table-cell",
  "2xl": "hidden 2xl:table-cell",
};

const SORTABLE: Record<string, SortKey> = {
  severity: "severity",
  status: "status",
  started: "started",
  resolution: "resolution",
  title: "severity",
};

/*
  Every column is offered in the menu, including the ones the responsive
  defaults drop. Selecting one there sets it in `hidden`'s opposite sense — the
  user override is tracked separately from the responsive default, so choosing
  "Root cause" on a phone genuinely shows it rather than being silently ignored
  by `lg:table-cell`.
*/
const TOGGLEABLE: ColumnId[] = COLUMNS.map((c) => c.key);

/**
 * The incident table.
 *
 * Eight columns, not fifteen. The root-cause column is intentionally the widest
 * text on the screen after the title: what was actually diagnosed is the thing
 * an operator scans for.
 *
 * Each row is one link. The accessible name is the incident id, and the link's
 * clickable area is stretched across the row with an `::after` overlay, so a
 * pointer user can click anywhere on the row while keyboard and screen-reader
 * users still get a single correctly-labelled link rather than a click handler
 * bolted onto a `<tr>`. The overlay stops short of the header, so it does not
 * swallow the sort buttons.
 */
export function IncidentTable({
  incidents,
  emptyAction,
}: {
  incidents: Incident[];
  emptyAction?: React.ReactNode;
}) {
  const [sortKey, setSortKey] = React.useState<SortKey>("severity");
  const [ascending, setAscending] = React.useState(false);
  const [status, setStatus] = React.useState<string>("all");
  const [service, setService] = React.useState<string>("all");
  const [hidden, setHidden] = React.useState<ColumnId[]>([]);
  /** Columns the operator has explicitly switched on, overriding the responsive default. */
  const [forced, setForced] = React.useState<ColumnId[]>([]);

  const services = React.useMemo(
    () => Array.from(new Set(incidents.map((i) => i.service))).sort(),
    [incidents],
  );
  const statuses = React.useMemo(
    () => Array.from(new Set(incidents.map((i) => i.status))).sort(),
    [incidents],
  );

  const visible = React.useMemo(() => {
    const filtered = incidents.filter(
      (i) =>
        (status === "all" || i.status === status) &&
        (service === "all" || i.service === service),
    );

    const direction = ascending ? 1 : -1;
    return [...filtered].sort((a, b) => {
      switch (sortKey) {
        case "severity":
          return (
            (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9) || direction
          );
        case "status":
          return a.status.localeCompare(b.status) * direction;
        case "resolution": {
          // Unresolved incidents have no duration; park them at the end
          // regardless of direction rather than treating them as zero.
          const left = a.resolution_time_seconds;
          const right = b.resolution_time_seconds;
          if (left === null || left === undefined) return right === null || right === undefined ? 0 : 1;
          if (right === null || right === undefined) return -1;
          return (left - right) * direction;
        }
        case "started":
        default: {
          const left = new Date(incidentTimestamp(a) ?? 0).getTime();
          const right = new Date(incidentTimestamp(b) ?? 0).getTime();
          return (left - right) * direction;
        }
      }
    });
  }, [incidents, sortKey, ascending, status, service]);

  function toggleSort(key: ColumnId) {
    const next = SORTABLE[key];
    if (!next) return;
    if (next === sortKey) {
      setAscending((prev) => !prev);
    } else {
      setSortKey(next);
      setAscending(next === "resolution");
    }
  }

  const isFiltered = status !== "all" || service !== "all";
  const shown = COLUMNS.filter((c) => !hidden.includes(c.key));

  /*
    Header and body must agree on which columns exist. Applying the responsive
    rule in both places from this one helper is what keeps the `<th>` count equal
    to the `<td>` count; setting it only on the body leaves an eight-column head
    over a six-column body, which silently clips the right-hand cells.

    A column the operator has explicitly switched on drops its responsive
    default, so the menu always wins over the layout.
  */
  const columnClasses = (column: (typeof COLUMNS)[number]) =>
    cn(
      column.className,
      column.hideBelow &&
        !forced.includes(column.key) &&
        RESPONSIVE_HIDE[column.hideBelow],
    );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-36" aria-label="Filter by status">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {statuses.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={service} onValueChange={setService}>
          <SelectTrigger className="w-44" aria-label="Filter by service">
            <SelectValue placeholder="Service" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All services</SelectItem>
            {services.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {isFiltered ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setStatus("all");
              setService("all");
            }}
          >
            Clear filters
          </Button>
        ) : null}

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            {visible.length} of {incidents.length} incidents
          </span>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Columns3Icon data-icon="inline-start" />
                <span className="hidden lg:inline">Columns</span>
                <span className="sr-only lg:hidden">Choose columns</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuLabel>Columns</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {TOGGLEABLE.map((id) => (
                <DropdownMenuCheckboxItem
                  key={id}
                  checked={!hidden.includes(id)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setHidden((prev) => prev.filter((c) => c !== id));
                      setForced((prev) =>
                        prev.includes(id) ? prev : [...prev, id],
                      );
                    } else {
                      setHidden((prev) =>
                        prev.includes(id) ? prev : [...prev, id],
                      );
                      setForced((prev) => prev.filter((c) => c !== id));
                    }
                  }}
                >
                  {COLUMNS.find((c) => c.key === id)?.label}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {incidents.length === 0 ? (
        <EmptyState
          title="No incidents recorded"
          message="Nothing has been logged yet. Run the learning-loop demo from the command center, or create an incident to begin."
          action={emptyAction}
        />
      ) : visible.length === 0 ? (
        <EmptyState
          title="No incidents match these filters"
          message="Clear the filters to see the full list."
        />
      ) : (
        // Cell padding is halved on a phone. At `px-4` the six visible columns
        // spend ~190px on padding alone, which is what pushed the table to
        // roughly twice the width of a 390px screen and left the last column
        // needing a horizontal scroll to reach.
        <div className="overflow-hidden rounded-lg border [&_td]:px-2 [&_th]:px-2 sm:[&_td]:px-4 sm:[&_th]:px-4">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                {shown.map((column) => {
                  const sortable = Boolean(SORTABLE[column.key]);
                  const active = sortKey === SORTABLE[column.key];
                  const Icon = !active
                    ? ArrowUpDownIcon
                    : ascending
                      ? ArrowUpIcon
                      : ArrowDownIcon;
                  return (
                    <TableHead
                      key={column.key}
                      className={columnClasses(column)}
                    >
                      {sortable ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="-ml-2 h-7 px-2 text-xs"
                          onClick={() => toggleSort(column.key)}
                        >
                          {column.label}
                          <Icon className="size-3 opacity-60" />
                        </Button>
                      ) : (
                        column.label
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((incident) => (
                <TableRow key={incident.id} className="group relative">
                  {shown.map((column) => {
                    switch (column.key) {
                      case "id":
                        return (
                          <TableCell key="id">
                            <Link
                              href={`/incidents/${incident.id}`}
                              className="font-mono text-[11px] text-muted-foreground after:absolute after:inset-0 after:content-[''] focus-visible:underline"
                            >
                              {incident.id}
                            </Link>
                          </TableCell>
                        );
                      case "title":
                        return (
                          <TableCell
                            key="title"
                            className="max-w-[9rem] sm:max-w-[18rem] lg:max-w-[22rem]"
                          >
                            <span className="truncate text-sm font-medium group-hover:underline">
                              {incident.title}
                            </span>
                          </TableCell>
                        );
                      case "service":
                        return (
                          <TableCell key="service" className={cn(columnClasses(column), "text-sm")}>
                            {incident.service}
                          </TableCell>
                        );
                      case "severity":
                        return (
                          <TableCell key="severity">
                            <SeverityBadge severity={incident.severity} />
                          </TableCell>
                        );
                      case "status":
                        return (
                          <TableCell key="status">
                            <StatusBadge status={incident.status} />
                          </TableCell>
                        );
                      case "started":
                        return (
                          <TableCell
                            key="started"
                            className={cn(
                              columnClasses(column),
                              "whitespace-nowrap text-xs text-muted-foreground",
                            )}
                          >
                            {formatRelative(incidentTimestamp(incident))}
                          </TableCell>
                        );
                      case "root_cause":
                        return (
                          <TableCell key="root_cause" className={columnClasses(column)}>
                            {/* "Not yet diagnosed" is a real finding about the incident,
                                not filler, so it is rendered at full muted strength. The
                                wording carries the de-emphasis. */}
                            {incident.root_cause ? (
                              <span
                                className="line-clamp-1 text-xs text-muted-foreground"
                                title={incident.root_cause}
                              >
                                {incident.root_cause}
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground">
                                Not yet diagnosed
                              </span>
                            )}
                          </TableCell>
                        );
                      case "resolution":
                      default:
                        return (
                          <TableCell key="resolution" className="text-right">
                            {incident.resolution_time_seconds ? (
                              <span className="tabular text-xs">
                                {formatDuration(incident.resolution_time_seconds)}
                              </span>
                            ) : (
                              <Badge variant="muted">—</Badge>
                            )}
                          </TableCell>
                        );
                    }
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

export { COLUMNS as INCIDENT_TABLE_COLUMNS };
