"use client";

import { useEffect, useRef, useState } from "react";
import { useConversation, useSendMessage } from "@/hooks/useChat";
import { ConversationSidebar } from "./ConversationSidebar";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { LoadingState, EmptyState } from "@/components/shared/LoadingState";
import type { ChatMessage } from "@/types";

export function ChatWindow({ projectId }: { projectId: string }) {
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const { data: conversation, isLoading } = useConversation(conversationId);
  const sendMessage = useSendMessage(projectId);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([]);

  const handleSend = (message: string) => {
    const tempId = `temp-${Date.now()}`;
    setOptimisticMessages((prev) => [
      ...prev,
      {
        id: tempId,
        role: "user",
        content: message,
        citations: null,
        created_at: new Date().toISOString(),
      },
    ]);

    sendMessage.mutate(
      { message, conversationId },
      {
        onSuccess: (data) => {
          setConversationId(data.conversation_id);
          setOptimisticMessages([]);
        },
        onError: () => {
          setOptimisticMessages([]);
        },
      }
    );
  };

  const handleSelectConversation = (id: string) => {
    setConversationId(id);
    setOptimisticMessages([]);
  };

  const handleNewChat = () => {
    setConversationId(undefined);
    setOptimisticMessages([]);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages, optimisticMessages]);

  const messages: ChatMessage[] = [
    ...(conversation?.messages ?? []),
    ...optimisticMessages,
  ];

  return (
    <div className="flex h-[calc(100vh-10rem)] overflow-hidden rounded-lg border border-border">
      {/* Conversation history sidebar */}
      <ConversationSidebar
        projectId={projectId}
        activeConversationId={conversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewChat}
      />

      {/* Chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {isLoading && conversationId ? (
            <LoadingState label="Loading conversation…" />
          ) : messages.length === 0 ? (
            <EmptyState
              title="Ask anything about your documents"
              description="Answers are grounded only in what you've uploaded — never hallucinated — with citations."
            />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}

          {sendMessage.isPending && (
            <p className="pl-11 text-xs text-muted-foreground animate-pulse">
              Searching documents and generating answer…
            </p>
          )}

          {sendMessage.isError && (
            <p className="pl-11 text-xs text-red-600">
              {(sendMessage.error as Error)?.message ?? "Something went wrong. Try again."}
            </p>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="border-t border-border p-4">
          <ChatInput onSend={handleSend} isSending={sendMessage.isPending} />
        </div>
      </div>
    </div>
  );
}
