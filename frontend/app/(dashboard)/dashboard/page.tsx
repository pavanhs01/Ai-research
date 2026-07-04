"use client";
export const dynamic = "force-dynamic";

import Link from "next/link";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useProjects } from "@/hooks/useProjects";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";

export default function DashboardPage() {
  const { data: user, isLoading: isLoadingUser, isError, error } = useCurrentUser();
  const { data: projects, isLoading: isLoadingProjects } = useProjects();

  if (isLoadingUser) return <LoadingState label="Loading your profile..." />;
  if (isError) return <ErrorState message={error?.message ?? "Failed to load profile"} />;

  const documentCount = projects?.reduce((sum, p) => sum + p.document_count, 0) ?? 0;
  const conversationCount = projects?.reduce((sum, p) => sum + p.conversation_count, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome back{user?.full_name ? `, ${user.full_name}` : ""}</h1>
        <p className="text-sm text-muted-foreground">{user?.email}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Projects" value={isLoadingProjects ? "…" : String(projects?.length ?? 0)} />
        <StatCard label="Documents" value={isLoadingProjects ? "…" : String(documentCount)} />
        <StatCard label="Conversations" value={isLoadingProjects ? "…" : String(conversationCount)} />
      </div>

      {!isLoadingProjects && projects?.length === 0 ? (
        <Link
          href="/projects"
          className="block rounded-lg border border-dashed border-border p-10 text-center text-sm text-muted-foreground hover:bg-muted/30"
        >
          Create your first project to start uploading documents and chatting with them.
        </Link>
      ) : (
        <Link href="/projects" className="inline-block text-sm font-medium text-primary hover:underline">
          Go to your projects →
        </Link>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border p-5">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}