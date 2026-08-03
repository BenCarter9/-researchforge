import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const base =
  "inline-flex items-center justify-center rounded-sm px-4 py-2.5 text-sm font-medium tracking-wide transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-mist";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-ink text-surface hover:bg-ink/90 focus-visible:ring-accent",
  secondary:
    "bg-surface text-ink border border-rule hover:border-ink/40 focus-visible:ring-rule",
  ghost:
    "bg-transparent text-accent hover:text-ink underline-offset-4 hover:underline focus-visible:ring-accent",
};

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  return <button className={cn(base, variants[variant], className)} {...props} />;
}
