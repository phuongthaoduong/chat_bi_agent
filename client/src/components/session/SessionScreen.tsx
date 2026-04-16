import type { UploadResponse } from "../../types";
import { DashboardView } from "./DashboardView";
import { FileInfoBar } from "./FileInfoBar";

interface SessionScreenProps {
  data: UploadResponse;
  onReset: () => void;
}

export function SessionScreen({ data, onReset }: SessionScreenProps) {
  return (
    <div style={{ minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <h1 style={{ fontSize: "20px", margin: 0 }}>ChatBI</h1>
        <button
          onClick={onReset}
          style={{
            padding: "6px 16px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            background: "white",
            cursor: "pointer",
          }}
        >
          New Upload
        </button>
      </div>
      <FileInfoBar profiles={data.profiles} warnings={data.warnings} />
      <DashboardView insights={data.insights} charts={data.charts} />
    </div>
  );
}
