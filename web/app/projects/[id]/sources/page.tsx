import Link from "next/link";

import { AddTranscript } from "@/components/AddTranscript";
import { Card } from "@/components/ui/Card";

export default async function SourcesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-lg px-4 py-12 sm:py-16">
      <Link
        href="/"
        className="font-display text-lg tracking-tight text-ink transition-colors hover:text-accent"
      >
        ResearchForge
      </Link>
      <h1 className="mt-8 font-display text-3xl tracking-tight text-ink">Add sources</h1>
      <p className="mt-2 font-serif text-mute">
        Upload an earnings-call transcript to ground management claims.
      </p>
      <Card className="mt-8">
        <AddTranscript projectId={id} />
      </Card>
    </main>
  );
}
