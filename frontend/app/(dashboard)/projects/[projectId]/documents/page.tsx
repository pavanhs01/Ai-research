"use client";
export const dynamic = "force-dynamic";

import { useParams } from "next/navigation";
import { useDocuments } from "@/hooks/useDocuments";
import { ProjectTabs } from "@/components/projects/ProjectTabs";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentList } from "@/components/documents/DocumentList";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";

export default function ProjectDocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: documents, isLoading, isError, error } = useDocuments(projectId);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Documents</h1>
      <ProjectTabs projectId={projectId} />
      <div className="space-y-6 pt-2">
        <UploadDropzone projectId={projectId} />
        {isLoading && <LoadingState label="Loading documents..." />}
        {isError && <ErrorState message={error?.message ?? "Failed to load documents"} />}
        {!isLoading && documents && <DocumentList projectId={projectId} documents={documents} />}
      </div>
    </div>
  );
}