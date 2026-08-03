import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "block w-full rounded-sm border border-rule bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-mute/70 focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink/30",
        className
      )}
      {...props}
    />
  );
}
