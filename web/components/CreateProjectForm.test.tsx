import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { CreateProjectForm } from "./CreateProjectForm";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/lib/api", () => ({
  createProject: vi.fn(),
}));

import { createProject } from "@/lib/api";

describe("CreateProjectForm", () => {
  beforeEach(() => {
    pushMock.mockReset();
    vi.mocked(createProject).mockReset();
  });

  it("submits trimmed company/ticker and routes to the sources page on success", async () => {
    vi.mocked(createProject).mockResolvedValue({
      project_id: "proj-123",
      company: "Acme Corp",
      ticker: "ACME",
    });
    const user = userEvent.setup();

    render(<CreateProjectForm />);

    await user.type(screen.getByLabelText(/^company/i), "  Acme Corp  ");
    await user.type(screen.getByLabelText(/^ticker/i), "  acme  ");
    await user.click(screen.getByRole("button", { name: /create project/i }));

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledTimes(1);
    });

    expect(createProject).toHaveBeenCalledWith(
      expect.objectContaining({ company: "Acme Corp", ticker: "acme" })
    );

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/projects/proj-123/sources");
    });
  });

  it("allows company-only submit (ticker optional)", async () => {
    vi.mocked(createProject).mockResolvedValue({
      project_id: "proj-456",
      company: "Apple Inc.",
      ticker: "AAPL",
    });
    const user = userEvent.setup();

    render(<CreateProjectForm />);

    await user.type(screen.getByLabelText(/^company/i), "Apple Inc.");
    await user.click(screen.getByRole("button", { name: /create project/i }));

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith(
        expect.objectContaining({ company: "Apple Inc.", ticker: undefined })
      );
    });
  });

  it("shows an inline error when neither company nor ticker is provided", async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm />);
    await user.click(screen.getByRole("button", { name: /create project/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/company name, a ticker, or both/i);
    expect(createProject).not.toHaveBeenCalled();
  });

  it("shows an inline error and does not navigate when createProject rejects (e.g. 422)", async () => {
    vi.mocked(createProject).mockRejectedValue(
      new Error("Unknown ticker: 'ZZZZ'")
    );
    const user = userEvent.setup();

    render(<CreateProjectForm />);

    await user.type(screen.getByLabelText(/^company/i), "Acme Corp");
    await user.type(screen.getByLabelText(/^ticker/i), "ZZZZ");
    await user.click(screen.getByRole("button", { name: /create project/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Unknown ticker: 'ZZZZ'");

    expect(pushMock).not.toHaveBeenCalled();
  });
});
