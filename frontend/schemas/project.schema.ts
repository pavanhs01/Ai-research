import { z } from "zod";

export const projectCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().max(4000).optional(),
});

export const projectSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  owner_id: z.string().uuid(),
  created_at: z.string(),
  updated_at: z.string(),
  document_count: z.number().default(0),
  conversation_count: z.number().default(0),
});

export type ProjectCreateInput = z.infer<typeof projectCreateSchema>;
export type Project = z.infer<typeof projectSchema>;
