import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  isLoading: boolean;
  error: string | null;
}

export function FileDropzone({ onFilesSelected, isLoading, error }: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) onFilesSelected(files);
    },
    [onFilesSelected]
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) onFilesSelected(files);
    },
    [onFilesSelected]
  );

  return (
    <div
      className={[
        "dropzone",
        isDragOver ? "dropzone--hover" : "",
        isLoading ? "dropzone--loading" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
    >
      {isLoading ? (
        <>
          <div className="loading-dots">
            <div className="loading-dot" />
            <div className="loading-dot" />
            <div className="loading-dot" />
          </div>
          <p className="loading-label">Analysing your data…</p>
          <p className="loading-sublabel">Building dashboard with AI</p>
        </>
      ) : (
        <>
          <svg
            className="dropzone-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p className="dropzone-title">Drop files here or click to upload</p>
          <p className="dropzone-hint">.csv · .xlsx · .xls · max 5 MB</p>
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls"
            onChange={handleFileInput}
            style={{ display: "none" }}
            id="file-input"
          />
          <label htmlFor="file-input" className="dropzone-btn">
            Choose Files
          </label>
        </>
      )}
      {error && <p className="dropzone-error">{error}</p>}
    </div>
  );
}
