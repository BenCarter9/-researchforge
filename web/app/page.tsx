import Link from "next/link";

export default function HomePage() {
  return (
    <main className="relative mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
      <div className="animate-fade-up">
        <p className="font-sans text-[0.7rem] font-medium uppercase tracking-[0.2em] text-mute">
          Evidence-grounded equity research
        </p>
        <h1 className="mt-4 font-display text-6xl tracking-tight text-ink sm:text-7xl md:text-8xl">
          ResearchForge
        </h1>
        <p className="mt-6 max-w-xl font-serif text-xl leading-relaxed text-mute">
          Enter a ticker and upload an earnings transcript. Get a source-backed
          research skeleton where every material claim links to its passage.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link
            href="/projects/new"
            className="inline-flex items-center rounded-sm bg-ink px-5 py-3 font-sans text-sm font-medium text-surface transition-colors hover:bg-ink/90"
          >
            Start a project
          </Link>
          <Link
            href="/desk"
            className="inline-flex items-center rounded-sm border border-rule bg-surface px-5 py-3 font-sans text-sm font-medium text-ink transition-colors hover:border-ink/40"
          >
            Open the desk
          </Link>
          <span className="font-sans text-xs tracking-wide text-mute">
            Snapshot · Business · Financials · Risks
          </span>
        </div>
      </div>
    </main>
  );
}
