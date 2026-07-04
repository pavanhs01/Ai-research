"use client";

import { useState } from "react";
import { FileText, ChevronDown } from "lucide-react";
import type { Citation } from "@/types";

export function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);

  const location = [citation.filename, citation.page_number ? `p. ${citation.page_number}` : null, citation.section]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="rounded-md border border-border text-xs">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-muted"
      >
        <FileText size={12} className="shrink-0 text-muted-foreground" />
        <span className="flex-1 truncate text-muted-foreground">
          [{index + 1}] {location}
        </span>
        <ChevronDown size={12} className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <p className="border-t border-border bg-muted/40 px-3 py-2 text-muted-foreground">
          &ldquo;{citation.snippet}&rdquo;
        </p>
      )}
    </div>
  );
}
