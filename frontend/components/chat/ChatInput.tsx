"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Send, Loader2 } from "lucide-react";
import { chatMessageSchema, type ChatMessageInput } from "@/schemas/chat.schema";

export function ChatInput({ onSend, isSending }: { onSend: (message: string) => void; isSending: boolean }) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChatMessageInput>({ resolver: zodResolver(chatMessageSchema) });

  const submit = (data: ChatMessageInput) => {
    onSend(data.message);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-1">
      <div className="flex items-end gap-2">
        <textarea
          {...register("message")}
          rows={2}
          placeholder="Ask a question about your documents..."
          className="flex-1 resize-none rounded-lg border border-border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(submit)();
            }
          }}
        />
        <button
          type="submit"
          disabled={isSending}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {isSending ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
        </button>
      </div>
      {errors.message && <p className="text-xs text-red-600">{errors.message.message}</p>}
    </form>
  );
}
