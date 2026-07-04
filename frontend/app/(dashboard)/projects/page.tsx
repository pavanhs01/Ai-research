"use client";
export const dynamic = "force-dynamic";

import { useProjects } from "@/hooks/useProjects";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { NewProjectDialog } from "@/components/projects/NewProjectDialog";
import { LoadingState, ErrorState, EmptyState } from "@/components/shared/LoadingState";

export default function ProjectsPage() {
  const { data: projects, isLoading, isError, error } = useProjects();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <NewProjectDialog />
      </div>

      {isLoading && <LoadingState label="Loading projects..." />}
      {isError && <ErrorState message={error?.message ?? "Failed to load projects"} />}
      {!isLoading && !isError && projects?.length === 0 && (
        <EmptyState
          title="No projects yet"
          description="Create your first research workspace to start uploading documents."
        />
      )}
      {!isLoading && projects && projects.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
    </div>
  );
}