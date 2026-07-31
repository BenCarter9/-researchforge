import { CreateProjectForm } from "@/components/CreateProjectForm";
import { Card } from "@/components/ui/Card";

export default function NewProjectPage() {
  return (
    <main className="mx-auto max-w-lg px-4 py-12">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">New research project</h1>
      <Card>
        <CreateProjectForm />
      </Card>
    </main>
  );
}
