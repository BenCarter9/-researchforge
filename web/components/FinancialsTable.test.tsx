import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FinancialsTable } from "./FinancialsTable";
import type { FinancialRow } from "@/lib/types";

describe("FinancialsTable", () => {
  it("renders numeric cells formatted with thousands separators and yoy as a percentage", () => {
    const table: FinancialRow[] = [
      {
        metric: "Revenue",
        key: "revenue",
        values: { FY2024: 1234567, FY2025: 1500000 },
        yoy: 0.18,
      },
    ];

    render(<FinancialsTable table={table} />);

    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getByText("1,234,567")).toBeInTheDocument();
    expect(screen.getByText("1,500,000")).toBeInTheDocument();
    expect(screen.getByText("+18.0%")).toBeInTheDocument();
  });

  it('renders missing cells as the literal word "unavailable", never 0', () => {
    const table: FinancialRow[] = [
      {
        metric: "Revenue",
        key: "revenue",
        values: { FY2024: 1234567, FY2025: 1500000 },
        yoy: 0.18,
      },
      {
        metric: "Net income",
        key: "net_income",
        values: { FY2024: "unavailable", FY2025: 250000 },
        yoy: "unavailable",
      },
    ];

    render(<FinancialsTable table={table} />);

    expect(screen.getByText("Net income")).toBeInTheDocument();
    expect(screen.getByText("250,000")).toBeInTheDocument();

    // The FY2024 net income cell and the yoy cell are both "unavailable".
    const unavailableCells = screen.getAllByText("unavailable");
    expect(unavailableCells.length).toBe(2);

    // Never render 0 for a missing fact.
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("still renders row labels with unavailable cells when a row has no data at all", () => {
    const table: FinancialRow[] = [
      {
        metric: "Gross margin",
        key: "gross_margin",
        values: {},
        yoy: "unavailable",
      },
    ];

    render(<FinancialsTable table={table} />);

    expect(screen.getByText("Gross margin")).toBeInTheDocument();
    expect(screen.getByText("unavailable")).toBeInTheDocument();
  });
});
