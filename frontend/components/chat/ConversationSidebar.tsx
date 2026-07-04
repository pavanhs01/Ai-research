"use client";

import { useState } from "react";
import { MessageSquare, Pencil, Plus, Trash2 } from "lucide-react";
import { useConversations, useDeleteConversation, useRenameConversation } from "@/hooks/useChat";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/types";

interface ConversationSidebarProps {
  projectId: string;
  activeConversationId?: string;
  onSelect: (conversationId: string) => void;
  onNew: () => void;
}

export function ConversationSidebar({
  projectId,
  activeConversationId,
  onSelect,
  onNew,
}: ConversationSidebarProps) {
  const { data: conversations, isLoading } = useConversations(projectId);
  const deleteConversation = useDeleteConversation(projectId);
  const renameConversation = useRenameConversation(projectId);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");

  const startEditing = (conv: Conversation) => {
    setEditingId(conv.id);
    setDraftTitle(conv.title);
  };

  const commitRename = (conversationId: string) => {
    const title = draftTitle.trim();
    setEditingId(null);
    if (title) {
      renameConversation.mutate({ conversationId, title });
    }
  };

  return (
    <div className="flex h-full w-56 shrink-0 flex-col border-r border-border">
      <div className="p-3">
        <button
          onClick={onNew}
          className="flex w-full items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          <Plus size={14} /> New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {isLoading && (
          <p className="px-2 text-xs text-muted-foreground">Loading…</p>
        )}
        {conversations?.map((conv: Conversation) => (
          <div
            key={conv.id}
            className={cn(
              "group relative flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left text-xs transition-colors",
              activeConversationId === conv.id
                ? "bg-muted font-medium"
                : "text-muted-foreground hover:bg-muted/60"
            )}
          >
            {editingId === conv.id ? (
              <input
                autoFocus
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                onBlur={() => commitRename(conv.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitRename(conv.id);
                  if (e.key === "Escape") setEditingId(null);
                }}
                className="flex-1 rounded border border-border bg-background px-1 py-0.5 text-xs outline-none"
              />
            ) : (
              <button onClick={() => onSelect(conv.id)} className="flex flex-1 items-start gap-2 text-left">
                <MessageSquare size={12} className="mt-0.5 shrink-0" />
                <span className="line-clamp-2 pr-8">{conv.title}</span>
              </button>
            )}

            {editingId !== conv.id && (
              <div className="absolute right-1.5 top-1.5 flex items-center gap-0.5 opacity-0 group-hover:opacity-100">
                <button
                  onClick={() => startEditing(conv)}
                  className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <Pencil size={12} />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete "${conv.title}"? This cannot be undone.`)) {
                      deleteConversation.mutate(conv.id, {
                        onSuccess: () => {
                          if (activeConversationId === conv.id) onNew();
                        },
                      });
                    }
                  }}
                  className="rounded-md p-1 text-muted-foreground hover:bg-red-50 hover:text-red-600"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            )}
          </div>
        ))}
        {!isLoading && conversations?.length === 0 && (
          <p className="px-2 text-xs text-muted-foreground">No conversations yet.</p>
        )}
      </div>
    </div>
  );
}
