"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { Menu } from "lucide-react";
import { useState } from "react";
import { Sidebar } from "./Sidebar";

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <header className="flex h-14 items-center justify-between border-b border-border px-4 md:hidden">
        <Link href="/dashboard" className="text-sm font-semibold">
          Research Assistant
        </Link>
        <div className="flex items-center gap-3">
          <UserButton afterSignOutUrl="/" />
          <button onClick={() => setMobileOpen(true)} className="text-muted-foreground">
            <Menu size={20} />
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full">
            <Sidebar />
          </div>
        </div>
      )}
    </>
  );
}
