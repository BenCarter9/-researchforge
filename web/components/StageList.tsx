import { humanizeStageName } from "@/lib/pipeline";
import { cn } from "@/lib/cn";
import type { StageStatus } from "@/lib/types";

export interface StageListProps {
  stages: StageStatus[];
}

const statusLabel: Record<StageStatus["status"], string> = {
  pending: "Pending",
  running: "In progress",
  done: "Done",
  error: "Error",
};

function StatusIcon({ status }: { status: StageStatus["status"] }) {
  if (status === "done") {
    return (
      <span
        aria-hidden="true"
        className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-sm bg-[var(--good)]/15 text-[0.65rem] text-[var(--good)]"
      >
        ✓
      </span>
    );
  }
  if (status === "error") {
    return (
      <span
        aria-hidden="true"
        className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-sm bg-[var(--bad)]/15 text-[0.65rem] text-[var(--bad)]"
      >
        ✕
      </span>
    );
  }
  if (status === "running") {
    return (
      <span
        aria-hidden="true"
        className="mt-0.5 h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-rule border-t-accent"
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="mt-0.5 h-4 w-4 shrink-0 rounded-full border border-rule"
    />
  );
}

export function StageList({ stages }: StageListProps) {
  if (stages.length === 0) {
    return <p className="text-sm text-mute">Waiting to start…</p>;
  }

  return (
    <ul className="space-y-2">
      {stages.map((stage) => (
        <li
          key={stage.stage}
          className={cn(
            "flex items-start gap-3 border-b border-rule/70 px-1 py-3 last:border-b-0",
            stage.status === "pending" && "opacity-55"
          )}
        >
          <StatusIcon status={stage.status} />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink">
              {humanizeStageName(stage.stage)}
              <span className="ml-2 text-xs font-normal text-mute">
                {statusLabel[stage.status]}
              </span>
            </p>
            {stage.status === "error" && stage.error && (
              <p role="alert" className="mt-1 text-sm text-[var(--bad)]">
                {stage.error}
              </p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
