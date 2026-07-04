"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { Project } from "@/types";
import type { ProjectCreateInput } from "@/schemas/project.schema";

export function useProjects() {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => request<Project[]>("/api/v1/projects"),
  });
}

export function useProject(projectId: string | undefined) {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => request<Project>(`/api/v1/projects/${projectId}`),
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProjectCreateInput) =>
      request<Project>("/api/v1/projects", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDeleteProject() {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => request<void>(`/api/v1/projects/${projectId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}
