import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StageList } from "./StageList";
import type { StageStatus } from "@/lib/types";

describe("StageList", () => {
  it("renders an error stage distinctly, with the error message in an alert", () => {
    const stages: StageStatus[] = [
      { stage: "fetch_filing", status: "done", error: null },
      { stage: "chunk", status: "error", error: "boom" },
      { stage: "extract_claims", status: "pending", error: null },
    ];

    render(<StageList stages={stages} />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("boom");

    // Stage names are humanized.
    expect(screen.getByText("Fetch filing")).toBeInTheDocument();
    expect(screen.getByText("Chunk")).toBeInTheDocument();
    expect(screen.getByText("Extract claims")).toBeInTheDocument();

    // Done and pending stages are both present.
    expect(screen.getByText("Done")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("shows a placeholder when there are no stages yet", () => {
    render(<StageList stages={[]} />);
    expect(screen.getByText(/waiting to start/i)).toBeInTheDocument();
  });

  it("renders a running stage with an in-progress indicator", () => {
    const stages: StageStatus[] = [
      { stage: "analyze", status: "running", error: null },
    ];
    render(<StageList stages={stages} />);
    expect(screen.getByText("Analyze")).toBeInTheDocument();
    expect(screen.getByText("In progress")).toBeInTheDocument();
  });
});
