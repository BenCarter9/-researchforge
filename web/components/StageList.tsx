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
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700"
      >
        ✓
      </span>
    );
  }
  if (status === "error") {
    return (
      <span
        aria-hidden="true"
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-700"
      >
        ✕
      </span>
    );
  }
  if (status === "running") {
    return (
      <span
        aria-hidden="true"
        className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="h-5 w-5 shrink-0 rounded-full border-2 border-slate-200"
    />
  );
}

export function StageList({ stages }: StageListProps) {
  if (stages.length === 0) {
    return <p className="text-sm text-slate-500">Waiting to start…</p>;
  }

  return (
    <ul className="space-y-3">
      {stages.map((stage) => (
        <li
          key={stage.stage}
          className={cn(
            "flex items-start gap-3 rounded-md border px-4 py-3",
            stage.status === "error"
              ? "border-red-200 bg-red-50"
              : stage.status === "done"
                ? "border-emerald-200 bg-emerald-50"
                : stage.status === "running"
                  ? "border-slate-300 bg-slate-50"
                  : "border-slate-200 bg-white"
          )}
        >
          <StatusIcon status={stage.status} />
          <div className="min-w-0 flex-1">
            <p
              className={cn(
                "text-sm font-medium",
                stage.status === "pending" ? "text-slate-400" : "text-slate-900"
              )}
            >
              {humanizeStageName(stage.stage)}
              <span className="ml-2 text-xs font-normal text-slate-400">
                {statusLabel[stage.status]}
              </span>
            </p>
            {stage.status === "error" && stage.error && (
              <p role="alert" className="mt-1 text-sm text-red-700">
                {stage.error}
              </p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
