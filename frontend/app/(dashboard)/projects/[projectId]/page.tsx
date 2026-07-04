"use client";
export const dynamic = "force-dynamic";

import { useParams } from "next/navigation";
import { useProject } from "@/hooks/useProjects";
import { ProjectTabs } from "@/components/projects/ProjectTabs";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";

export default function ProjectOverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project, isLoading, isError, error } = useProject(projectId);

  if (isLoading) return <LoadingState label="Loading project..." />;
  if (isError) return <ErrorState message={error?.message ?? "Failed to load project"} />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">{project?.name}</h1>
        {project?.description && <p className="text-sm text-muted-foreground">{project.description}</p>}
      </div>
      <ProjectTabs projectId={projectId} />
      <p className="pt-4 text-sm text-muted-foreground">
        Use the Documents tab to upload sources, then ask questions in Chat or search directly below.
      </p>
    </div>
  );
}