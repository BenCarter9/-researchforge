import { AddTranscript } from "@/components/AddTranscript";
import { Card } from "@/components/ui/Card";

export default async function SourcesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-lg px-4 py-12">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">Add sources</h1>
      <Card>
        <AddTranscript projectId={id} />
      </Card>
    </main>
  );
}
