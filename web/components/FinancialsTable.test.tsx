import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

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

  it("renders clickable YoY that exposes the engine formula", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    const table: FinancialRow[] = [
      {
        metric: "Revenue",
        key: "revenue",
        values: { FY2023: 307394, FY2024: 350018 },
        yoy: 0.1387,
        yoy_calc: {
          metric: "growth",
          formula: "(curr - prev) / prev",
          inputs: { curr: 350018, prev: 307394 },
          result: 0.1387,
          unit: "ratio",
          period: null,
        },
      },
    ];
    render(<FinancialsTable table={table} onOpenFormula={onOpen} />);
    await user.click(screen.getByRole("button", { name: /\+13\.9%/ }));
    expect(onOpen).toHaveBeenCalledWith(
      expect.objectContaining({
        metric: "Revenue",
        calc: expect.objectContaining({ formula: "(curr - prev) / prev" }),
      })
    );
  });
});
