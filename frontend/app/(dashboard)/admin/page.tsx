"use client";
export const dynamic = "force-dynamic";


import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useAdminUsers } from "@/hooks/useAdminUsers";
import { useAdminStats } from "@/hooks/useAdminStats";
import { LoadingState, ErrorState, EmptyState } from "@/components/shared/LoadingState";

export default function AdminPage() {
  const { data: currentUser, isLoading: isLoadingMe } = useCurrentUser();
  const isAdmin = currentUser?.role === "admin";
  const { data: stats } = useAdminStats();
  const { data: users, isLoading, isError, error } = useAdminUsers();

  if (isLoadingMe) return <LoadingState label="Checking permissions…" />;

  if (!isAdmin) {
    return <ErrorState message="Admin access required." />;
  }

  if (isLoading) return <LoadingState label="Loading users…" />;
  if (isError) return <ErrorState message={error?.message ?? "Failed to load users"} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Admin Dashboard</h1>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-4">
          <StatCard label="Total users" value={stats.total_users} />
          <StatCard label="Projects" value={stats.total_projects} />
          <StatCard label="Documents" value={stats.total_documents} />
          <StatCard label="Paying subscribers" value={stats.paying_subscribers} />
        </div>
      )}

      <div>
        <h2 className="mb-3 text-lg font-medium">Users</h2>
        {!users || users.length === 0 ? (
          <EmptyState title="No users yet" />
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Email</th>
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">Role</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-4 py-2">{u.email}</td>
                    <td className="px-4 py-2">{u.full_name ?? "—"}</td>
                    <td className="px-4 py-2 capitalize">{u.role}</td>
                    <td className="px-4 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}>
                        {u.is_active ? "Active" : "Deactivated"}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}