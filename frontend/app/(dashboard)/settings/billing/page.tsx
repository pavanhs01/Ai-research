"use client";
export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";

import { useSubscription, useBillingPortal } from "@/hooks/useSubscription";
import { PlanCard } from "@/components/billing/PlanCard";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import type { PlanTier } from "@/types";
import { Loader2 } from "lucide-react";

const PLANS: PlanTier[] = ["free", "pro", "team"];

export default function BillingPage() {
  const { data: subscription, isLoading, isError, error } = useSubscription();
  const portal = useBillingPortal();

  if (isLoading) return <LoadingState label="Loading billing info..." />;
  if (isError) return <ErrorState message={error?.message ?? "Failed to load billing info"} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-medium">Plans</h2>
        {subscription?.plan !== "free" && (
          <button
            onClick={() =>
              portal.mutate(undefined, { onSuccess: (d) => (window.location.href = d.portal_url) })
            }
            disabled={portal.isPending}
            className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
          >
            {portal.isPending && <Loader2 size={14} className="animate-spin" />}
            Manage subscription
          </button>
        )}
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {PLANS.map((plan) => (
          <PlanCard key={plan} plan={plan} isCurrent={subscription?.plan === plan} />
        ))}
      </div>
    </div>
  );
}
