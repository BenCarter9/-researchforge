"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { draftDeskMemo } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { DeskCall, DeskMemo, DeskPayload } from "@/lib/types";

type Confirmation = "unconfirmed" | "confirmed" | "rejected";

export function DeskView({ desk }: { desk: DeskPayload }) {
  const [memo, setMemo] = useState<DeskMemo>(desk.precomputed);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmations, setConfirmations] = useState<Record<string, Confirmation>>(
    () => Object.fromEntries(desk.calls.map((call) => [call.id, "unconfirmed"]))
  );

  async function handleDraft() {
    setBusy(true);
    setError(null);
    try {
      setMemo(await draftDeskMemo());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Draft failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <p className="max-w-2xl font-serif text-lg leading-relaxed text-mute">
        Model drafts. You confirm. Two sourced workflow-tool calls — not public
        equities, and not invented financials.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        {desk.calls.map((call) => (
          <CallCard
            key={call.id}
            call={call}
            confirmation={confirmations[call.id] ?? "unconfirmed"}
            onConfirm={(next) =>
              setConfirmations((prev) => ({ ...prev, [call.id]: next }))
            }
          />
        ))}
      </div>

      <Card>
        <p className="font-sans text-[0.7rem] font-medium uppercase tracking-[0.18em] text-mute">
          Optional memo draft
        </p>
        <h2 className="mt-2 font-display text-2xl tracking-tight text-ink">
          GLM-5.2{" "}
          <span className="font-sans text-base font-medium text-mute">
            {desk.model_id}
          </span>
        </h2>
        <p className="mt-2 font-sans text-sm text-mute">
          Open weights, {desk.model_license} license.{" "}
          <a
            href={desk.weights_url}
            className="text-accent underline-offset-4 hover:underline"
          >
            Hugging Face
          </a>
          . OpenAI-compatible API when a key is set.
        </p>

        {memo.source === "precomputed" ? (
          <p
            role="status"
            className="mt-4 border border-[var(--warn)]/40 bg-[var(--warn)]/10 px-3 py-2 font-sans text-sm text-[var(--warn)]"
          >
            {memo.label}
          </p>
        ) : (
          <p
            role="status"
            className="mt-4 border border-[var(--good)]/30 bg-[var(--good)]/10 px-3 py-2 font-sans text-sm text-[var(--good)]"
          >
            {memo.label}
          </p>
        )}

        <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap border border-rule bg-mist/60 p-4 font-sans text-sm leading-relaxed text-ink">
          {memo.draft}
        </pre>

        <details className="mt-4">
          <summary className="cursor-pointer font-sans text-sm font-medium text-accent">
            Exact prompt and model id
          </summary>
          <dl className="mt-3 space-y-2 font-sans text-xs text-mute">
            <div>
              <dt className="font-medium text-ink">model_id</dt>
              <dd>
                <code>{desk.model_id}</code>
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ink">system</dt>
              <dd>
                <pre className="mt-1 whitespace-pre-wrap border border-rule bg-surface p-3">
                  {desk.system_prompt}
                </pre>
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ink">user</dt>
              <dd>
                <pre className="mt-1 max-h-72 overflow-auto whitespace-pre-wrap border border-rule bg-surface p-3">
                  {desk.prompt}
                </pre>
              </dd>
            </div>
          </dl>
        </details>

        {error && (
          <p role="alert" className="mt-4 text-sm text-[var(--bad)]">
            {error}
          </p>
        )}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button type="button" onClick={handleDraft} disabled={busy}>
            {busy
              ? "Drafting…"
              : desk.live_available
                ? "Draft with live GLM-5.2"
                : "Re-show precomputed draft"}
          </Button>
          <span className="font-sans text-xs text-mute">
            {desk.live_available
              ? `Live key: ${desk.key_name}`
              : "No API key — screen recording can still show model id + prompt."}
          </span>
        </div>
      </Card>
    </div>
  );
}

function CallCard({
  call,
  confirmation,
  onConfirm,
}: {
  call: DeskCall;
  confirmation: Confirmation;
  onConfirm: (next: Confirmation) => void;
}) {
  const take = call.proposed === "TAKE";
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p
            className={cn(
              "font-sans text-[0.7rem] font-medium uppercase tracking-[0.18em]",
              take ? "text-[var(--good)]" : "text-mute"
            )}
          >
            Draft {call.proposed}
          </p>
          <h2 className="mt-2 font-display text-3xl tracking-tight text-ink">
            {call.company}
          </h2>
          <p className="mt-1 font-serif text-mute">{call.headline}</p>
        </div>
        <ConfirmationBadge status={confirmation} />
      </div>

      <p className="mt-4 font-serif text-[1.05rem] leading-relaxed text-ink">
        {call.summary}
      </p>

      <ul className="mt-5 space-y-4">
        {call.facts.map((fact) => (
          <li key={fact.id} className="border-t border-rule/70 pt-4">
            <p className="font-serif text-sm leading-relaxed text-ink">{fact.text}</p>
            <p className="mt-2 font-sans text-xs text-mute">
              {fact.source.publisher} · {fact.source.date} · {fact.kind.replace(/_/g, " ")}
            </p>
            <blockquote className="mt-2 border-l-2 border-accent/50 pl-3 font-serif text-sm italic text-mute">
              “{fact.source.verbatim_quote}”
            </blockquote>
            <a
              href={fact.source.url}
              className="mt-2 inline-block font-sans text-xs font-medium text-accent underline-offset-4 hover:underline"
            >
              Source
            </a>
          </li>
        ))}
      </ul>

      {call.unverified.length > 0 && (
        <div className="mt-4 border border-rule bg-mist/50 p-3">
          <p className="font-sans text-[0.65rem] font-medium uppercase tracking-[0.16em] text-[var(--warn)]">
            Unverified — not treated as fact
          </p>
          {call.unverified.map((note) => (
            <p key={note} className="mt-1 font-sans text-xs text-mute">
              {note}
            </p>
          ))}
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        <Button
          type="button"
          variant={confirmation === "confirmed" ? "primary" : "secondary"}
          onClick={() => onConfirm("confirmed")}
        >
          Confirm {call.proposed}
        </Button>
        <Button
          type="button"
          variant={confirmation === "rejected" ? "primary" : "ghost"}
          onClick={() => onConfirm("rejected")}
        >
          Reject draft
        </Button>
      </div>
    </Card>
  );
}

function ConfirmationBadge({ status }: { status: Confirmation }) {
  const label =
    status === "confirmed"
      ? "Confirmed by you"
      : status === "rejected"
        ? "Rejected by you"
        : "Awaiting your call";
  return (
    <span
      className={cn(
        "shrink-0 font-sans text-[0.65rem] font-medium uppercase tracking-[0.14em]",
        status === "confirmed"
          ? "text-[var(--good)]"
          : status === "rejected"
            ? "text-[var(--bad)]"
            : "text-mute"
      )}
    >
      {label}
    </span>
  );
}
