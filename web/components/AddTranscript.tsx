"use client";

import { useRouter } from "next/navigation";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { startAnalysis, uploadTranscript } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export interface AddTranscriptProps {
  projectId: string;
}

export function AddTranscript({ projectId }: AddTranscriptProps) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [label, setLabel] = useState("transcript");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [chunkCount, setChunkCount] = useState<number | null>(null);

  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const fileText = await file.text();
    setText(fileText);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadError(null);
    setChunkCount(null);

    setIsUploading(true);
    try {
      const result = await uploadTranscript(projectId, {
        text,
        label: label.trim() || "transcript",
      });
      setChunkCount(result.chunk_count);
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to upload transcript."
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleGenerateReport() {
    setAnalysisError(null);
    setIsAnalyzing(true);
    try {
      await startAnalysis(projectId);
      router.push(`/projects/${projectId}/processing`);
    } catch (err) {
      setAnalysisError(
        err instanceof Error ? err.message : "Failed to start analysis."
      );
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleUpload} className="space-y-4">
        <div>
          <label htmlFor="transcript-text" className="mb-1 block text-sm font-medium text-slate-700">
            Paste transcript text
          </label>
          <textarea
            id="transcript-text"
            name="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            placeholder="Paste earnings call transcript here…"
          />
        </div>

        <div>
          <label htmlFor="transcript-file" className="mb-1 block text-sm font-medium text-slate-700">
            Or upload a file
          </label>
          <input
            id="transcript-file"
            name="file"
            type="file"
            accept=".txt,.md,text/plain"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-700 file:mr-4 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-900 hover:file:bg-slate-100"
          />
        </div>

        <div>
          <label htmlFor="transcript-label" className="mb-1 block text-sm font-medium text-slate-700">
            Label
          </label>
          <Input
            id="transcript-label"
            name="label"
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </div>

        {uploadError && (
          <p role="alert" className="text-sm text-red-600">
            {uploadError}
          </p>
        )}

        {chunkCount !== null && (
          <p className="text-sm text-emerald-600">
            Transcript added ({chunkCount} chunk{chunkCount === 1 ? "" : "s"}).
          </p>
        )}

        <Button type="submit" disabled={isUploading || !text.trim()}>
          {isUploading ? "Adding…" : "Add transcript"}
        </Button>
      </form>

      <div className="border-t border-slate-200 pt-6">
        {analysisError && (
          <p role="alert" className="mb-2 text-sm text-red-600">
            {analysisError}
          </p>
        )}
        <Button
          type="button"
          variant="secondary"
          onClick={handleGenerateReport}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? "Starting…" : "Generate report"}
        </Button>
      </div>
    </div>
  );
}
