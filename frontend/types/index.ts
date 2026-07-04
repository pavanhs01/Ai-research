export type UserRole = "user" | "admin";

export interface UserProfile {
  id: string;
  clerk_id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
  document_count: number;
  conversation_count: number;
}

export type DocumentStatus = "pending" | "parsing" | "chunking" | "embedding" | "indexed" | "failed";
export type DocumentSourceType = "pdf" | "docx" | "txt" | "markdown" | "url";

export interface AppDocument {
  id: string;
  project_id: string;
  filename: string;
  source_type: DocumentSourceType;
  source_url: string | null;
  mime_type: string | null;
  file_size_bytes: number | null;
  status: DocumentStatus;
  error_message: string | null;
  page_count: number | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  chunk_id: string;
  filename: string;
  page_number: number | null;
  section: string | null;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: ChatMessage[];
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: Citation[];
}

export interface SearchResult {
  chunk_id: string;
  filename: string;
  page_number: number | null;
  section: string | null;
  content: string;
  score: number;
}

export type PlanTier = "free" | "pro" | "team";
export type SubscriptionStatus = "active" | "trialing" | "past_due" | "canceled" | "incomplete";

export interface Subscription {
  plan: PlanTier;
  status: SubscriptionStatus;
  current_period_end: string | null;
}
