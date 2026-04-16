import type { SheetProfile } from "../../types";

interface FileInfoBarProps {
  profiles: SheetProfile[];
  warnings: string[];
}

export function FileInfoBar({ profiles, warnings }: FileInfoBarProps) {
  return (
    <div style={{ borderBottom: "1px solid #e5e7eb", padding: "16px 24px" }}>
      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
        {profiles.map((profile, i) => (
          <div
            key={i}
            style={{
              padding: "12px 16px",
              backgroundColor: "#f9fafb",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: "4px" }}>
              {profile.file_name}
              {profile.sheet_name !== "Sheet1" && ` / ${profile.sheet_name}`}
            </div>
            <div style={{ fontSize: "14px", color: "#6b7280" }}>
              {profile.row_count.toLocaleString()} rows · {profile.column_count} columns
            </div>
            <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>
              {profile.columns.map((c) => c.name).join(", ")}
            </div>
          </div>
        ))}
      </div>
      {warnings.map((w, i) => (
        <div
          key={i}
          style={{
            marginTop: "8px",
            padding: "8px 12px",
            backgroundColor: "#fef3c7",
            borderRadius: "6px",
            fontSize: "14px",
            color: "#92400e",
          }}
        >
          {w}
        </div>
      ))}
    </div>
  );
}
