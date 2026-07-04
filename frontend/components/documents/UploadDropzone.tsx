"use client";

import { useRef, useState } from "react";
import { UploadCloud, Link as LinkIcon, Loader2 } from "lucide-react";
import { useUploadDocument, useIngestUrl } from "@/hooks/useDocuments";

export function UploadDropzone({ projectId }: { projectId: string }) {
  const [isDragging, setIsDragging] = useState(false);
  const [url, setUrl] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = useUploadDocument(projectId);
  const ingestUrl = useIngestUrl(projectId);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    Array.from(files).forEach((file) => upload.mutate(file));
  };

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    ingestUrl.mutate(url.trim());
    setUrl("");
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50"
        }`}
      >
        {upload.isPending ? (
          <Loader2 className="animate-spin text-muted-foreground" size={28} />
        ) : (
          <UploadCloud className="text-muted-foreground" size={28} />
        )}
        <p className="text-sm font-medium">Drop files here or click to browse</p>
        <p className="text-xs text-muted-foreground">PDF, DOCX, TXT, Markdown — up to 25MB</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.markdown"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {upload.isError && (
        <p className="text-sm text-red-600">{(upload.error as Error)?.message ?? "Upload failed"}</p>
      )}

      <form onSubmit={handleUrlSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Or paste a URL to ingest"
            className="w-full rounded-lg border border-border py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button
          type="submit"
          disabled={ingestUrl.isPending}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {ingestUrl.isPending ? "Adding..." : "Add URL"}
        </button>
      </form>
    </div>
  );
}
