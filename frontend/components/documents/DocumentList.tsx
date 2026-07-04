"use client";

import { useState } from "react";
import { FileText, Trash2, Sparkles, Loader2 } from "lucide-react";
import { useDeleteDocument, useGenerateSummary } from "@/hooks/useDocuments";
import { DocumentStatusBadge } from "./DocumentStatusBadge";
import type { AppDocument } from "@/types";
import { EmptyState } from "@/components/shared/LoadingState";

export function DocumentList({ projectId, documents }: { projectId: string; documents: AppDocument[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const deleteDoc = useDeleteDocument(projectId);
  const generateSummary = useGenerateSummary(projectId);

  if (documents.length === 0) {
    return <EmptyState title="No documents yet" description="Upload a file or add a URL above to get started." />;
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div key={doc.id} className="rounded-lg border border-border">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3 overflow-hidden">
              <FileText size={18} className="shrink-0 text-muted-foreground" />
              <div className="overflow-hidden">
                <p className="truncate text-sm font-medium">{doc.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {doc.page_count ? `${doc.page_count} pages · ` : ""}
                  {doc.source_type.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <DocumentStatusBadge status={doc.status} />
              {doc.status === "indexed" && (
                <button
                  onClick={() => {
                    setExpandedId(expandedId === doc.id ? null : doc.id);
                    if (!doc.summary) generateSummary.mutate(doc.id);
                  }}
                  className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
                  title="Summarize"
                >
                  {generateSummary.isPending && expandedId === doc.id ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Sparkles size={16} />
                  )}
                </button>
              )}
              <button
                onClick={() => deleteDoc.mutate(doc.id)}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-600"
                title="Delete"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {doc.status === "failed" && doc.error_message && (
            <p className="border-t border-border bg-red-50 px-4 py-2 text-xs text-red-600">{doc.error_message}</p>
          )}

          {expandedId === doc.id && doc.summary && (
            <div className="border-t border-border bg-muted/30 p-4 text-sm">
              <p className="mb-1 font-medium">AI Summary</p>
              <p className="whitespace-pre-wrap text-muted-foreground">{doc.summary}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
