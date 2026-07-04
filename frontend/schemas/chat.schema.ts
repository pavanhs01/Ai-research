import { z } from "zod";

export const chatMessageSchema = z.object({
  message: z.string().min(1, "Type a message").max(8000),
});

export const citationSchema = z.object({
  chunk_id: z.string().uuid(),
  filename: z.string(),
  page_number: z.number().nullable(),
  section: z.string().nullable(),
  snippet: z.string(),
});

export type ChatMessageInput = z.infer<typeof chatMessageSchema>;
export type Citation = z.infer<typeof citationSchema>;
