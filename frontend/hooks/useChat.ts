"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "@/lib/api-client";
import type { ChatResponse, Conversation, ConversationWithMessages } from "@/types";

export function useConversations(projectId: string | undefined) {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["conversations", projectId],
    queryFn: () => request<Conversation[]>(`/api/v1/chat/conversations/${projectId}`),
    enabled: !!projectId,
  });
}

export function useConversation(conversationId: string | undefined) {
  const { request } = useApiClient();
  return useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => request<ConversationWithMessages>(`/api/v1/chat/conversations/detail/${conversationId}`),
    enabled: !!conversationId,
  });
}

export function useSendMessage(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ message, conversationId }: { message: string; conversationId?: string }) =>
      request<ChatResponse>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, conversation_id: conversationId ?? null, message }),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["conversation", data.conversation_id] });
      queryClient.invalidateQueries({ queryKey: ["conversations", projectId] });
    },
  });
}

export function useDeleteConversation(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) =>
      request<void>(`/api/v1/chat/conversations/${conversationId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", projectId] });
    },
  });
}

export function useRenameConversation(projectId: string) {
  const { request } = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, title }: { conversationId: string; title: string }) =>
      request<Conversation>(`/api/v1/chat/conversations/${conversationId}`, {
        method: "PATCH",
        body: JSON.stringify({ title }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", projectId] });
    },
  });
}
