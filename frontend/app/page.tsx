import Link from "next/link";
import { SignedIn, SignedOut } from "@clerk/nextjs";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
        Your documents. Answered with citations.
      </h1>
      <p className="max-w-xl text-muted-foreground">
        Upload PDFs, DOCX, and notes. Ask questions in plain English. Get answers
        grounded only in your own sources — never hallucinated.
      </p>
      <div className="flex gap-4">
        <SignedOut>
          <Link
            href="/sign-up"
            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Get started free
          </Link>
          <Link
            href="/sign-in"
            className="rounded-lg border border-border px-5 py-2.5 text-sm font-medium hover:bg-muted"
          >
            Sign in
          </Link>
        </SignedOut>
        <SignedIn>
          <Link
            href="/dashboard"
            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Go to dashboard
          </Link>
        </SignedIn>
      </div>
    </main>
  );
}
