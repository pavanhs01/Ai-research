import Link from "next/link";
import { FileText, MessageSquare, Trash2 } from "lucide-react";
import type { Project } from "@/types";
import { useDeleteProject } from "@/hooks/useProjects";

export function ProjectCard({ project }: { project: Project }) {
  const deleteProject = useDeleteProject();

  return (
    <div className="group relative rounded-lg border border-border p-5 transition-colors hover:bg-muted/30">
      <Link href={`/projects/${project.id}`} className="block">
        <h3 className="font-medium">{project.name}</h3>
        {project.description && (
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{project.description}</p>
        )}
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <FileText size={12} /> {project.document_count}
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare size={12} /> {project.conversation_count}
          </span>
        </div>
      </Link>
      <button
        onClick={(e) => {
          e.preventDefault();
          if (confirm(`Delete "${project.name}"? This removes all its documents and conversations.`)) {
            deleteProject.mutate(project.id);
          }
        }}
        className="absolute right-3 top-3 rounded-md p-1.5 text-muted-foreground opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}
