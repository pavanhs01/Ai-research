"use client";
export const dynamic = "force-dynamic";

import { useParams } from "next/navigation";
import { ProjectTabs } from "@/components/projects/ProjectTabs";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ProjectChatPage() {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Chat</h1>
      <ProjectTabs projectId={projectId} />
      <div className="pt-2">
        <ChatWindow projectId={projectId} />
      </div>
    </div>
  );
}