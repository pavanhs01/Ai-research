"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Loader2 } from "lucide-react";
import { projectCreateSchema, type ProjectCreateInput } from "@/schemas/project.schema";
import { useCreateProject } from "@/hooks/useProjects";

export function NewProjectDialog() {
  const [open, setOpen] = useState(false);
  const createProject = useCreateProject();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectCreateInput>({ resolver: zodResolver(projectCreateSchema) });

  const submit = (data: ProjectCreateInput) => {
    createProject.mutate(data, {
      onSuccess: () => {
        reset();
        setOpen(false);
      },
    });
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
      >
        <Plus size={16} /> New project
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="space-y-3 rounded-lg border border-border p-4"
    >
      <div>
        <input
          {...register("name")}
          placeholder="Project name"
          autoFocus
          className="w-full rounded-lg border border-border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
        />
        {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
      </div>
      <textarea
        {...register("description")}
        placeholder="Description (optional)"
        rows={2}
        className="w-full resize-none rounded-lg border border-border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
      />
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={createProject.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {createProject.isPending && <Loader2 size={14} className="animate-spin" />}
          Create
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
