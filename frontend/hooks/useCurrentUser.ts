"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { UserProfile } from "@/types";

export function useCurrentUser() {
  const { request } = useApiClient();

  return useQuery({
    queryKey: ["me"],
    queryFn: () => request<UserProfile>("/api/v1/me"),
  });
}
