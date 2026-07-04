"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";

interface PlatformStats {
  total_users: number;
  total_projects: number;
  total_documents: number;
  paying_subscribers: number;
}

export function useAdminStats() {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => request<PlatformStats>("/api/v1/admin/stats"),
  });
}
