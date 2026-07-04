import Link from "next/link";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <nav className="mt-2 flex gap-4 border-b border-border pb-2">
          <Link
            href="/settings/billing"
            className="text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            Billing
          </Link>
        </nav>
      </div>
      {children}
    </div>
  );
}
