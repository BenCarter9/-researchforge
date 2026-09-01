import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SourceViewer } from "./SourceViewer";
import type { Chunk } from "@/lib/types";
import { getChunk, markCitation } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  getChunk: vi.fn(),
  markCitation: vi.fn(),
}));

const mockGetChunk = vi.mocked(getChunk);
const mockMarkCitation = vi.mocked(markCitation);

const baseChunk: Chunk = {
  document_id: "d1",
  section_label: "prepared_remarks_cfo",
  page_start: 3,
  page_end: 4,
  speaker: "Jane Doe",
  text: "Alpha BETA gamma",
};

describe("SourceViewer", () => {
  beforeEach(() => {
    mockGetChunk.mockReset();
    mockMarkCitation.mockReset();
  });

  it("highlights exactly the quote substring within the chunk text", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await waitFor(() => expect(mockGetChunk).toHaveBeenCalledWith("c1"));

    const marks = await screen.findAllByText("BETA", { selector: "mark" });
    expect(marks).toHaveLength(1);
    expect(marks[0].tagName).toBe("MARK");
    expect(marks[0].textContent).toBe("BETA");

    // Surrounding, non-highlighted text is still present.
    expect(screen.getByText(/Alpha/)).toBeInTheDocument();
    expect(screen.getByText(/gamma/)).toBeInTheDocument();

    // The claim it supports is rendered.
    expect(screen.getByText("Revenue grew.")).toBeInTheDocument();
  });

  it("renders a provided passage immediately without a loading flash", () => {
    mockGetChunk.mockReturnValue(new Promise(() => {}));
    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
        passage="Alpha BETA gamma"
        sectionLabel="item_1"
      />
    );
    expect(screen.queryByText(/Loading source/i)).not.toBeInTheDocument();
    expect(screen.getByText("BETA", { selector: "mark" })).toBeInTheDocument();
  });

  it("shows a loading state before the chunk resolves", () => {
    mockGetChunk.mockReturnValue(new Promise(() => {}));

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    expect(screen.getByText(/Loading source/i)).toBeInTheDocument();
  });

  it("shows an inline error message when the chunk fails to load", async () => {
    mockGetChunk.mockRejectedValue(new Error("chunk not found"));

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    expect(await screen.findByText("chunk not found")).toBeInTheDocument();
  });

  it("highlights across whitespace differences (multiple spaces / newline) between the quote and the chunk text", async () => {
    const whitespaceChunk: Chunk = {
      ...baseChunk,
      text: "Alpha   BETA\ngamma delta",
    };
    mockGetChunk.mockResolvedValue(whitespaceChunk);

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA gamma"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await waitFor(() => expect(mockGetChunk).toHaveBeenCalledWith("c1"));

    const marks = await waitFor(() => {
      const found = document.querySelectorAll("mark");
      expect(found).toHaveLength(1);
      return found;
    });
    expect(marks).toHaveLength(1);
    expect(marks[0].tagName).toBe("MARK");
    // The highlighted span is the ORIGINAL text (with its internal
    // whitespace/newline preserved), not the normalized quote.
    expect(marks[0].textContent).toBe("BETA\ngamma");

    expect(screen.queryByText(/quote not located/i)).not.toBeInTheDocument();
  });

  it("does not highlight and shows a note when the quote is not found in the chunk text", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);

    render(
      <SourceViewer
        chunkId="c1"
        quote="not in the text anywhere"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await screen.findByText(baseChunk.text);

    expect(document.querySelectorAll("mark")).toHaveLength(0);
    expect(screen.getByText(/quote not located/i)).toBeInTheDocument();
  });

  it('calling "Mark valid" calls markCitation with the citation id and true', async () => {
    mockGetChunk.mockResolvedValue(baseChunk);
    mockMarkCitation.mockResolvedValue({ ok: true });

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    fireEvent.click(screen.getByRole("button", { name: /mark valid/i }));

    await waitFor(() =>
      expect(mockMarkCitation).toHaveBeenCalledWith("cit-1", true)
    );
  });

  it('calling "Mark invalid" calls markCitation with the citation id and false', async () => {
    mockGetChunk.mockResolvedValue(baseChunk);
    mockMarkCitation.mockResolvedValue({ ok: true });

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    fireEvent.click(screen.getByRole("button", { name: /mark invalid/i }));

    await waitFor(() =>
      expect(mockMarkCitation).toHaveBeenCalledWith("cit-1", false)
    );
  });

  it("shows an inline error message when marking the citation fails", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);
    mockMarkCitation.mockRejectedValue(new Error("mark failed"));

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    fireEvent.click(screen.getByRole("button", { name: /mark valid/i }));

    expect(await screen.findByText("mark failed")).toBeInTheDocument();
  });

  it("renders the section label (humanized) and page range", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    expect(screen.getByText(/Prepared remarks cfo/i)).toBeInTheDocument();
    expect(screen.getByText(/3.*4/)).toBeInTheDocument();
  });

  it("resets stale marked state when a new citation shares the same chunk", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);
    mockMarkCitation.mockResolvedValue({ ok: true });

    const { rerender } = render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-A"
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    fireEvent.click(screen.getByRole("button", { name: /mark valid/i }));

    await waitFor(() =>
      expect(mockMarkCitation).toHaveBeenCalledWith("cit-A", true)
    );
    expect(await screen.findByText(/marked as valid/i)).toBeInTheDocument();

    // Re-render the same mounted component for a different citation that
    // happens to reference the SAME chunk_id. Because chunkId is unchanged,
    // a fix that only depends on [chunkId] would fail to reset `marked`.
    rerender(
      <SourceViewer
        chunkId="c1"
        quote="gamma"
        claimText="Costs fell."
        citationId="cit-B"
      />
    );

    await screen.findByText("gamma", { selector: "mark" });

    expect(screen.queryByText(/marked as valid/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/marked as invalid/i)).not.toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", async () => {
    mockGetChunk.mockResolvedValue(baseChunk);
    const onClose = vi.fn();

    render(
      <SourceViewer
        chunkId="c1"
        quote="BETA"
        claimText="Revenue grew."
        citationId="cit-1"
        onClose={onClose}
      />
    );

    await screen.findByText("BETA", { selector: "mark" });

    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
