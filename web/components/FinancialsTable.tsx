import type { FinancialRow } from "@/lib/types";

export interface FinancialsTableProps {
  table: FinancialRow[];
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

function formatNumber(value: number): string {
  return value.toLocaleString("en-US");
}

function formatYoy(value: number): string {
  const formatted = value.toFixed(1);
  return value >= 0 ? `+${formatted}%` : `${formatted}%`;
}

// Missing financial facts must always render as the literal word
// "unavailable" — never 0 and never a blank cell.
function ValueCell({ value }: { value: number | "unavailable" }) {
  if (value === "unavailable") {
    return <span className="text-slate-400">unavailable</span>;
  }
  return <span>{formatNumber(value)}</span>;
}

function YoyCell({ value }: { value: number | "unavailable" }) {
  if (value === "unavailable") {
    return <span className="text-slate-400">unavailable</span>;
  }
  const colorClass =
    value > 0 ? "text-emerald-700" : value < 0 ? "text-red-700" : "text-slate-700";
  return <span className={colorClass}>{formatYoy(value)}</span>;
}

export function FinancialsTable({ table }: FinancialsTableProps) {
  const years = yearKeys(table);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-max border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs font-medium uppercase tracking-wide text-slate-500">
            <th scope="col" className="py-2 pr-4 text-left">
              Metric
            </th>
            {years.map((year) => (
              <th key={year} scope="col" className="py-2 pr-4 text-right">
                {year}
              </th>
            ))}
            <th scope="col" className="py-2 pr-4 text-right">
              YoY
            </th>
          </tr>
        </thead>
        <tbody>
          {table.map((row) => (
            <tr key={row.key} className="border-b border-slate-100 last:border-b-0">
              <th scope="row" className="py-2 pr-4 text-left font-normal text-slate-900">
                {row.metric}
              </th>
              {years.map((year) => (
                <td key={year} className="py-2 pr-4 text-right tabular-nums">
                  <ValueCell value={row.values[year] ?? "unavailable"} />
                </td>
              ))}
              <td className="py-2 pr-4 text-right tabular-nums">
                <YoyCell value={row.yoy} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
