"use client";

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { SearchResult } from "@/types";

export function useSemanticSearch(projectId: string) {
  const { request } = useApiClient();

  return useMutation({
    mutationFn: (query: string) =>
      request<SearchResult[]>("/api/v1/search", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, query, top_k: 10 }),
      }),
  });
}
