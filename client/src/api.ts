import type { AddFilesResponse, ChatResponse, UploadResponse } from "./types";

const API_BASE = "/api";

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = "Upload failed";
    try { message = (await response.json()).error?.message || message; } catch {}
    throw new Error(message);
  }

  return response.json();
}

export async function addFilesToSession(
  sessionId: string,
  files: File[]
): Promise<AddFilesResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/session/${sessionId}/files`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = "Failed to add files";
    try { message = (await response.json()).error?.message || message; } catch {}
    throw new Error(message);
  }

  return response.json();
}

export async function askQuestion(
  sessionId: string,
  question: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });

  if (!response.ok) {
    let message = "Chat request failed";
    try { message = (await response.json()).error?.message || message; } catch {}
    throw new Error(message);
  }

  return response.json();
}
