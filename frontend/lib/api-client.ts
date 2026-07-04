"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) {
    super(message);
  }
}

/**
 * Returns a `request` function pre-bound with the current Clerk session
 * token. Use inside React Query hooks (see hooks/useDocuments.ts etc.)
 * rather than calling fetch() directly anywhere else in the app.
 */
export function useApiClient() {
  const { getToken } = useAuth();

  const request = useCallback(
    async <T,>(path: string, init?: RequestInit): Promise<T> => {
      const token = await getToken();
      const isFormData = init?.body instanceof FormData;

      const response = await fetch(`${API_URL}${path}`, {
        ...init,
        headers: {
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...init?.headers,
        },
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          body?.error?.message ?? "Request failed",
          body?.error?.code
        );
      }

      if (response.status === 204) return undefined as T;
      return response.json() as Promise<T>;
    },
    [getToken]
  );

  return { request };
}
