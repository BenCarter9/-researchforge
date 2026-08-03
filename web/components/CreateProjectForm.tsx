"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createProject } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function CreateProjectForm() {
  const router = useRouter();
  const [company, setCompany] = useState("");
  const [ticker, setTicker] = useState("");
  const [researchDate, setResearchDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedCompany = company.trim();
    const trimmedTicker = ticker.trim();

    if (!trimmedCompany && !trimmedTicker) {
      setError("Enter a company name, a ticker, or both.");
      return;
    }

    setIsPending(true);
    try {
      const { project_id } = await createProject({
        company: trimmedCompany || undefined,
        ticker: trimmedTicker || undefined,
        research_date: researchDate.trim() || undefined,
      });
      router.push(`/projects/${project_id}/sources`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project.");
      setIsPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <p className="text-sm text-mute">
        Provide a company name, a ticker, or both — we resolve the rest from SEC
        EDGAR.
      </p>

      <div>
        <label htmlFor="company" className="mb-1 block text-sm font-medium text-ink">
          Company{" "}
          <span className="font-normal text-mute">(optional if ticker is set)</span>
        </label>
        <Input
          id="company"
          name="company"
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Costco Wholesale"
        />
      </div>

      <div>
        <label htmlFor="ticker" className="mb-1 block text-sm font-medium text-ink">
          Ticker{" "}
          <span className="font-normal text-mute">(optional if company is set)</span>
        </label>
        <Input
          id="ticker"
          name="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="COST"
        />
      </div>

      <div>
        <label
          htmlFor="research-date"
          className="mb-1 block text-sm font-medium text-ink"
        >
          Research date <span className="font-normal text-mute">(optional)</span>
        </label>
        <Input
          id="research-date"
          name="research-date"
          type="date"
          value={researchDate}
          onChange={(e) => setResearchDate(e.target.value)}
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-[var(--bad)]">
          {error}
        </p>
      )}

      <Button type="submit" disabled={isPending}>
        {isPending ? "Creating…" : "Create project"}
      </Button>
    </form>
  );
}
