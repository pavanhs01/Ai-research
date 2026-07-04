import { z } from "zod";

export const documentStatusSchema = z.enum([
  "pending",
  "parsing",
  "chunking",
  "embedding",
  "indexed",
  "failed",
]);

export const documentSourceTypeSchema = z.enum(["pdf", "docx", "txt", "markdown", "url"]);

export const documentSchema = z.object({
  id: z.string().uuid(),
  project_id: z.string().uuid(),
  filename: z.string(),
  source_type: documentSourceTypeSchema,
  source_url: z.string().nullable(),
  mime_type: z.string().nullable(),
  file_size_bytes: z.number().nullable(),
  status: documentStatusSchema,
  error_message: z.string().nullable(),
  page_count: z.number().nullable(),
  summary: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const urlIngestSchema = z.object({
  project_id: z.string().uuid(),
  url: z.string().url("Enter a valid URL"),
});

export type Document = z.infer<typeof documentSchema>;
export type UrlIngestInput = z.infer<typeof urlIngestSchema>;
