"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { UserProfile } from "@/types";

export function useAdminUsers() {
  const { request } = useApiClient();

  return useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => request<UserProfile[]>("/api/v1/admin/users"),
  });
}
