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

    setIsPending(true);
    try {
      const { project_id } = await createProject({
        company: trimmedCompany,
        ticker: trimmedTicker,
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
      <div>
        <label htmlFor="company" className="mb-1 block text-sm font-medium text-slate-700">
          Company
        </label>
        <Input
          id="company"
          name="company"
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Apple Inc."
          required
        />
      </div>

      <div>
        <label htmlFor="ticker" className="mb-1 block text-sm font-medium text-slate-700">
          Ticker
        </label>
        <Input
          id="ticker"
          name="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="AAPL"
          required
        />
      </div>

      <div>
        <label htmlFor="research-date" className="mb-1 block text-sm font-medium text-slate-700">
          Research date <span className="font-normal text-slate-400">(optional)</span>
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
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <Button type="submit" disabled={isPending}>
        {isPending ? "Creating…" : "Create project"}
      </Button>
    </form>
  );
}
