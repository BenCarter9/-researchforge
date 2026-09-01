import type { FinancialRow, YoyCalc } from "@/lib/types";

export interface FinancialsTableProps {
  table: FinancialRow[];
  onOpenFormula?: (payload: { metric: string; calc: YoyCalc }) => void;
}

// Sorted, de-duplicated set of fiscal-year keys across every row (e.g.
// "FY2024", "FY2025", ...). Sorting is lexical, which is chronological for
// this "FY<year>" label shape.
function yearKeys(table: FinancialRow[]): string[] {
  const keys = new Set<string>();
  for (const row of table) {
    for (const key of Object.keys(row.values)) {
      keys.add(key);
    }
  }
  return Array.from(keys).sort();
}

function isRatioKey(key: string): boolean {
  return key.endsWith("_margin") || key === "revenue_cagr";
}

function formatNumber(value: number): string {
  return value.toLocaleString("en-US");
}

function formatRatio(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

// Backend YoY is a growth ratio (0.18), not a percentage point.
function formatYoy(value: number): string {
  const pct = value * 100;
  const formatted = pct.toFixed(1);
  return pct >= 0 ? `+${formatted}%` : `${formatted}%`;
}

// Missing financial facts must always render as the literal word
// "unavailable" — never 0 and never a blank cell.
function ValueCell({
  value,
  ratio,
}: {
  value: number | "unavailable";
  ratio: boolean;
}) {
  if (value === "unavailable") {
    return <span className="text-mute/70">unavailable</span>;
  }
  return <span>{ratio ? formatRatio(value) : formatNumber(value)}</span>;
}

function YoyCell({
  value,
  calc,
  metric,
  onOpen,
}: {
  value: number | "unavailable";
  calc?: YoyCalc | null;
  metric: string;
  onOpen?: (payload: { metric: string; calc: YoyCalc }) => void;
}) {
  if (value === "unavailable") {
    return <span className="text-mute/70">unavailable</span>;
  }
  const colorClass =
    value > 0 ? "text-[var(--good)]" : value < 0 ? "text-[var(--bad)]" : "text-ink";
  const label = formatYoy(value);
  if (calc && onOpen) {
    return (
      <button
        type="button"
        onClick={() => onOpen({ metric, calc })}
        className={`${colorClass} underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40`}
      >
        {label}
      </button>
    );
  }
  return <span className={colorClass}>{label}</span>;
}

export function FinancialsTable({ table, onOpenFormula }: FinancialsTableProps) {
  const years = yearKeys(table);

  return (
    <div className="overflow-x-auto">
      <p className="mb-3 font-sans text-[0.7rem] uppercase tracking-[0.12em] text-mute">
        Click a YoY figure to see the deterministic formula. Missing facts
        render as unavailable — never 0.
      </p>
      <table className="w-full min-w-max border-collapse font-sans text-sm">
        <thead>
          <tr className="border-b border-rule text-[0.7rem] font-medium uppercase tracking-[0.12em] text-mute">
            <th scope="col" className="py-3 pr-4 text-left">
              Metric
            </th>
            {years.map((year) => (
              <th key={year} scope="col" className="py-3 pr-4 text-right">
                {year}
              </th>
            ))}
            <th scope="col" className="py-3 pr-4 text-right">
              YoY
            </th>
          </tr>
        </thead>
        <tbody>
          {table.map((row) => (
            <tr key={row.key} className="border-b border-rule/60 last:border-b-0">
              <th
                scope="row"
                className="py-2.5 pr-4 text-left font-normal text-ink"
              >
                {row.metric}
              </th>
              {years.map((year) => (
                <td key={year} className="py-2.5 pr-4 text-right font-sans tabular-nums">
                  <ValueCell
                    value={row.values[year] ?? "unavailable"}
                    ratio={isRatioKey(row.key)}
                  />
                </td>
              ))}
              <td className="py-2.5 pr-4 text-right font-sans tabular-nums">
                <YoyCell
                  value={row.yoy}
                  calc={row.yoy_calc}
                  metric={row.metric}
                  onOpen={onOpenFormula}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
