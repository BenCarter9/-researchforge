import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ClaimLine } from "./ClaimLine";
import type { Claim } from "@/lib/types";

const cited: Claim = {
  id: "c1",
  claim_text: "Google Services generates revenue primarily from advertising.",
  claim_type: "reported_fact",
  evidence_status: "green",
  citation: {
    id: "cit-1",
    chunk_id: "chunk-1",
    verbatim_quote: "Google Services generates revenues primarily",
    verbatim_verified: true,
    passage: "Google Services generates revenues primarily by delivering ads.",
    section_label: "item_1",
  },
};

describe("ClaimLine", () => {
  it("opens the source drawer when the claim text is clicked", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    render(<ClaimLine claim={cited} onOpenCitation={onOpen} />);

    await user.click(
      screen.getByRole("button", {
        name: /google services generates revenue primarily from advertising/i,
      })
    );

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen.mock.calls[0][0]).toMatchObject({
      chunkId: "chunk-1",
      citationId: "cit-1",
      passage: "Google Services generates revenues primarily by delivering ads.",
    });
  });

  it("still opens the drawer from the Source control", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    render(<ClaimLine claim={cited} onOpenCitation={onOpen} />);
    await user.click(screen.getByRole("button", { name: /source/i }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});
