import { useState } from "react";
import { uploadFiles } from "../../api";
import { UploadResponse } from "../../types";
import { FileDropzone } from "./FileDropzone";

interface UploadScreenProps {
  onUploadComplete: (data: UploadResponse) => void;
}

export function UploadScreen({ onUploadComplete }: UploadScreenProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFilesSelected = async (files: File[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await uploadFiles(files);
      onUploadComplete(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "24px",
      }}
    >
      <h1 style={{ fontSize: "32px", marginBottom: "8px" }}>ChatBI</h1>
      <p style={{ color: "#6b7280", marginBottom: "32px" }}>
        Upload your data files to get started
      </p>
      <div style={{ width: "100%", maxWidth: "500px" }}>
        <FileDropzone
          onFilesSelected={handleFilesSelected}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}
