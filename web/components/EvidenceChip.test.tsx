import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceChip } from "./EvidenceChip";
import type { EvidenceStatus } from "@/lib/types";

const cases: Array<{
  status: EvidenceStatus;
  label: string;
  token: string;
}> = [
  { status: "green", label: "Supported", token: "--good" },
  { status: "yellow", label: "Inference / partial", token: "--warn" },
  { status: "red", label: "Unsupported", token: "--bad" },
  { status: "gray", label: "Assumption", token: "mute" },
];

describe("EvidenceChip", () => {
  for (const { status, label, token } of cases) {
    it(`status "${status}" renders the "${label}" label with a ${token} color token and no digit`, () => {
      render(<EvidenceChip status={status} />);

      const chip = screen.getByText(label);
      expect(chip).toBeInTheDocument();

      // Distinct visual token per status (Forge Ledger palette).
      expect(chip.className).toContain(token);

      // Guard against ever rendering a numeric confidence score.
      expect(chip.textContent ?? "").not.toMatch(/\d/);
    });
  }
});
