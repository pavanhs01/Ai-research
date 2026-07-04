"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { AppDocument } from "@/types";

export function useDocuments(projectId: string | undefined) {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => request<AppDocument[]>(`/api/v1/documents/project/${projectId}`),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      const stillProcessing = docs.some((d) => !["indexed", "failed"].includes(d.status));
      return stillProcessing ? 3000 : false;
    },
  });
}

export function useUploadDocument(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("project_id", projectId);
      formData.append("file", file);
      return request<{ id: string; filename: string; status: string }>("/api/v1/documents/upload", {
        method: "POST",
        body: formData,
      });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}

export function useIngestUrl(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (url: string) =>
      request("/api/v1/documents/ingest-url", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, url }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}

export function useDeleteDocument(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => request<void>(`/api/v1/documents/${documentId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}

export function useGenerateSummary(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      request<AppDocument>(`/api/v1/documents/${documentId}/summary`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });
}
