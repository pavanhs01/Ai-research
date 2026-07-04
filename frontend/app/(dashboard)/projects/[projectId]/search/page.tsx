"use client";
export const dynamic = "force-dynamic";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Search, Loader2 } from "lucide-react";
import { useSemanticSearch } from "@/hooks/useSearch";
import { ProjectTabs } from "@/components/projects/ProjectTabs";
import { EmptyState, ErrorState } from "@/components/shared/LoadingState";

export default function ProjectSearchPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [query, setQuery] = useState("");
  const search = useSemanticSearch(projectId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) search.mutate(query.trim());
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Semantic Search</h1>
      <ProjectTabs projectId={projectId} />

      <form onSubmit={handleSubmit} className="flex gap-2 pt-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across all your documents..."
            className="w-full rounded-lg border border-border py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button
          type="submit"
          disabled={search.isPending}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {search.isPending ? <Loader2 size={16} className="animate-spin" /> : "Search"}
        </button>
      </form>

      {search.isError && <ErrorState message={(search.error as Error)?.message ?? "Search failed"} />}

      {search.data && search.data.length === 0 && (
        <EmptyState title="No matches found" description="Try a different phrasing or check your spelling." />
      )}

      {search.data && search.data.length > 0 && (
        <div className="space-y-2">
          {search.data.map((result) => (
            <div key={result.chunk_id} className="rounded-lg border border-border p-4">
              <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  {result.filename}
                  {result.page_number ? ` · p. ${result.page_number}` : ""}
                  {result.section ? ` · ${result.section}` : ""}
                </span>
                <span>{Math.round(result.score * 100)}% match</span>
              </div>
              <p className="text-sm">{result.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}