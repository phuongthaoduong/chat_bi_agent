// FileInfoBar is superseded by the sidebar in the redesign.
// Kept for compatibility — not rendered in SessionScreen.

import type { SheetProfile } from "../../types";

interface FileInfoBarProps {
  profiles: SheetProfile[];
  warnings: string[];
}

export function FileInfoBar({ profiles, warnings }: FileInfoBarProps) {
  return (
    <div style={{ borderBottom: "1px solid var(--border)", padding: "12px 20px", background: "var(--surface)" }}>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {profiles.map((p, i) => (
          <div
            key={i}
            style={{
              padding: "8px 12px",
              background: "var(--surface-2)",
              border: "1px solid var(--border-2)",
              borderRadius: "var(--radius)",
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text)" }}>{p.file_name}</div>
            <div style={{ fontSize: 11, color: "var(--text-3)", fontFamily: "var(--font-mono)", marginTop: 2 }}>
              {p.row_count.toLocaleString()} rows · {p.column_count} cols
            </div>
          </div>
        ))}
      </div>
      {warnings.map((w, i) => (
        <div key={i} className="warning-chip">{w}</div>
      ))}
    </div>
  );
}
