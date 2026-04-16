import type { UploadResponse } from "./types";

const API_BASE = "/api";

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Upload failed");
  }

  return response.json();
}
