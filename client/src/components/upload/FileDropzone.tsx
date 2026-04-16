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
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      style={{
        border: `2px dashed ${isDragOver ? "#4f46e5" : "#d1d5db"}`,
        borderRadius: "12px",
        padding: "48px",
        textAlign: "center",
        cursor: isLoading ? "wait" : "pointer",
        backgroundColor: isDragOver ? "#eef2ff" : "#fafafa",
        transition: "all 0.2s",
      }}
    >
      {isLoading ? (
        <div>
          <div
            style={{
              width: "40px",
              height: "40px",
              border: "3px solid #e5e7eb",
              borderTopColor: "#4f46e5",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 12px",
            }}
          />
          <p style={{ fontSize: "16px", marginBottom: "4px" }}>Uploading and analyzing your data...</p>
          <p style={{ fontSize: "14px", color: "#6b7280" }}>This may take a few seconds</p>
        </div>
      ) : (
        <>
          <p style={{ fontSize: "18px", marginBottom: "8px" }}>
            Drop files here or click to upload
          </p>
          <p style={{ color: "#6b7280", fontSize: "14px" }}>
            Supports .csv, .xlsx, .xls (max 5MB)
          </p>
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls"
            onChange={handleFileInput}
            style={{ display: "none" }}
            id="file-input"
          />
          <label
            htmlFor="file-input"
            style={{
              display: "inline-block",
              marginTop: "16px",
              padding: "8px 24px",
              backgroundColor: "#4f46e5",
              color: "white",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            Choose Files
          </label>
        </>
      )}
      {error && (
        <p style={{ color: "#dc2626", marginTop: "12px" }}>{error}</p>
      )}
    </div>
  );
}
