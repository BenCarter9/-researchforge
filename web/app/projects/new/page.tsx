import Link from "next/link";

import { CreateProjectForm } from "@/components/CreateProjectForm";
import { Card } from "@/components/ui/Card";

export default function NewProjectPage() {
  return (
    <main className="mx-auto max-w-lg px-4 py-12 sm:py-16">
      <Link
        href="/"
        className="font-display text-lg tracking-tight text-ink transition-colors hover:text-accent"
      >
        ResearchForge
      </Link>
      <h1 className="mt-8 font-display text-3xl tracking-tight text-ink">
        New research project
      </h1>
      <p className="mt-2 font-serif text-mute">
        Resolve a public company ticker, then add an earnings transcript.
      </p>
      <Card className="mt-8">
        <CreateProjectForm />
      </Card>
    </main>
  );
}
