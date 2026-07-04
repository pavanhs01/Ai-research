"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { PlanTier, Subscription } from "@/types";

export function useSubscription() {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["subscription"],
    queryFn: () => request<Subscription>("/api/v1/billing/subscription"),
  });
}

export function useCreateCheckout() {
  const { request } = useApiClient();
  return useMutation({
    mutationFn: (plan: PlanTier) =>
      request<{ checkout_url: string }>("/api/v1/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      }),
  });
}

export function useBillingPortal() {
  const { request } = useApiClient();
  return useMutation({
    mutationFn: () => request<{ portal_url: string }>("/api/v1/billing/portal", { method: "POST" }),
  });
}
