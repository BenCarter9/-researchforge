import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceChip } from "./EvidenceChip";
import type { EvidenceStatus } from "@/lib/types";

const cases: Array<{
  status: EvidenceStatus;
  label: string;
  colorToken: string;
}> = [
  { status: "green", label: "Supported", colorToken: "green" },
  { status: "yellow", label: "Inference / partial", colorToken: "amber" },
  { status: "red", label: "Unsupported", colorToken: "red" },
  { status: "gray", label: "Assumption", colorToken: "gray" },
];

describe("EvidenceChip", () => {
  for (const { status, label, colorToken } of cases) {
    it(`status "${status}" renders the "${label}" label with a ${colorToken} color class and no digit`, () => {
      render(<EvidenceChip status={status} />);

      const chip = screen.getByText(label);
      expect(chip).toBeInTheDocument();

      // Color class per status.
      expect(chip.className).toContain(colorToken);

      // Guard against ever rendering a numeric confidence score.
      expect(chip.textContent ?? "").not.toMatch(/\d/);
    });
  }
});
