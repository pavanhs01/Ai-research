"use client";

import { Check, Loader2 } from "lucide-react";
import { useCreateCheckout } from "@/hooks/useSubscription";
import type { PlanTier } from "@/types";

const PLAN_DETAILS: Record<PlanTier, { name: string; price: string; features: string[] }> = {
  free: { name: "Free", price: "$0/mo", features: ["3 projects", "50 documents", "Basic chat"] },
  pro: { name: "Pro", price: "$29/mo", features: ["Unlimited projects", "1,000 documents", "Priority chat", "Citation highlighting"] },
  team: { name: "Team", price: "$99/mo", features: ["Everything in Pro", "5 seats", "Shared workspaces", "Admin controls"] },
};

export function PlanCard({ plan, isCurrent }: { plan: PlanTier; isCurrent: boolean }) {
  const checkout = useCreateCheckout();
  const details = PLAN_DETAILS[plan];

  const handleUpgrade = () => {
    checkout.mutate(plan, {
      onSuccess: (data) => {
        window.location.href = data.checkout_url;
      },
    });
  };

  return (
    <div className={`rounded-lg border p-5 ${isCurrent ? "border-primary" : "border-border"}`}>
      <h3 className="font-medium">{details.name}</h3>
      <p className="mt-1 text-2xl font-semibold">{details.price}</p>
      <ul className="mt-4 space-y-2">
        {details.features.map((f) => (
          <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
            <Check size={14} className="text-primary" /> {f}
          </li>
        ))}
      </ul>
      {plan !== "free" && !isCurrent && (
        <button
          onClick={handleUpgrade}
          disabled={checkout.isPending}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {checkout.isPending && <Loader2 size={14} className="animate-spin" />}
          Upgrade to {details.name}
        </button>
      )}
      {isCurrent && (
        <div className="mt-4 rounded-lg bg-muted px-4 py-2 text-center text-sm text-muted-foreground">
          Current plan
        </div>
      )}
    </div>
  );
}
