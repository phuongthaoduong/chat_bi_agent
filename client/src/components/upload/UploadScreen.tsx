import { useState } from "react";
import { uploadFiles } from "../../api";
import type { UploadResponse } from "../../types";
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
    <div className="upload-screen">
      <div className="upload-glow" />
      <div className="upload-content">
        <div className="upload-wordmark">
          Chat<em>BI</em>
        </div>
        <p className="upload-tagline">Query your data in plain English.</p>
        <div className="upload-zone-wrap">
          <FileDropzone
            onFilesSelected={handleFilesSelected}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}
