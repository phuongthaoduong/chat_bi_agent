import { useRef, useState, useMemo } from "react";
import type { UploadResponse, Message, ChartData } from "../../types";
import { addFilesToSession, askQuestion } from "../../api";
import { ChatView } from "./ChatView";
import { ChartCard } from "../shared/ChartCard";

interface SessionScreenProps {
  data: UploadResponse;
  onReset: () => void;
}

function buildInitialMessage(insights: string[]): Message | null {
  if (insights.length === 0) return null;
  const content = "Here's what I found in your data:\n\n" + insights.map((s) => `- ${s}`).join("\n");
  // No chart — the initial chart lives only in the Visualization panel, not in chat
  return { role: "assistant", content };
}

export function SessionScreen({ data, onReset }: SessionScreenProps) {
  const [sessionData, setSessionData] = useState(data);
  const [messages, setMessages] = useState<Message[]>(() => {
    const initial = buildInitialMessage(data.insights);
    return initial ? [initial] : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isAddingFile, setIsAddingFile] = useState(false);
  const [addFileError, setAddFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tracks the most recent dashboard chart (from upload or add-file) — panel only.
  const [dashboardChart, setDashboardChart] = useState<ChartData | null>(data.chart);

  // The visualization panel shows: the latest chart from chat responses,
  // falling back to the latest dashboard chart from upload/add-file.
  const latestChart = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant" && messages[i].chart) {
        return messages[i].chart!;
      }
    }
    return dashboardChart;
  }, [messages, dashboardChart]);

  const handleSendMessage = async (question: string) => {
    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    try {
      const response = await askQuestion(sessionData.session_id, question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          chart: response.chart,
          table: response.table,
          totalRows: response.total_rows,
          displayedRows: response.displayed_rows,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      if (message.includes("Session expired")) { onReset(); return; }
      setMessages((prev) => [...prev, { role: "assistant", content: message }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setAddFileError(null);
    setIsAddingFile(true);
    try {
      const result = await addFilesToSession(sessionData.session_id, Array.from(files));
      setSessionData((prev) => {
        const replacedSet = new Set(result.replaced);
        const keptProfiles = prev.profiles.filter(
          (p) => !replacedSet.has(p.file_name)
        );
        const keptFiles = prev.files.filter(
          (f) => !replacedSet.has(f.name)
        );
        return {
          ...prev,
          profiles: [...keptProfiles, ...result.profiles],
          files: [...keptFiles, ...result.files],
          warnings: [...prev.warnings, ...result.warnings],
        };
      });
      if (result.chart) setDashboardChart(result.chart);
      const newMsg = buildInitialMessage(result.insights);
      if (newMsg) {
        newMsg.content = `New file added. ${newMsg.content}`;
        setMessages((prev) => [...prev, newMsg]);
      }
    } catch (err) {
      setAddFileError(err instanceof Error ? err.message : "Failed to add file.");
    } finally {
      setIsAddingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="session-root">
      {/* ── Sticky top bar ── */}
      <header className="session-topbar">
        <div className="session-topbar-brand">
          Chat<em>BI</em>
        </div>
        <div className="session-topbar-tagline">Your data, explained.</div>
        <button className="panel-reset-btn" onClick={onReset}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          New session
        </button>
      </header>

      <div className="session-layout">
        {/* ── Left: Chat panel ── */}
        <div className="panel-chat">
          <ChatView messages={messages} onSend={handleSendMessage} isLoading={isLoading} />
        </div>

      {/* ── Right column ── */}
      <div className="panel-right">
        {/* ── Chart box ── */}
        <div className="panel-box panel-chart">
          <div className="panel-box-header">
            <div className="panel-box-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              Visualization
            </div>
          </div>

          <div className="panel-chart-body">
            {latestChart ? (
              <ChartCard data={latestChart} />
            ) : (
              <div className="panel-chart-empty">
                <div className="panel-chart-empty-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                </div>
                <p className="panel-chart-empty-text">
                  Charts will appear here when you ask data questions
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Files box ── */}
        <div className="panel-box panel-files">
          <div className="panel-box-header">
            <div className="panel-box-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              Data Sources
            </div>
            <span className="panel-box-count">{sessionData.profiles.length}</span>
          </div>

          <div className="panel-files-scroll">
            {sessionData.profiles.map((profile, i) => (
              <div key={i} className="file-card">
                <div className="file-card-icon">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <path d="M3 9h18M9 21V9" />
                  </svg>
                </div>
                <div className="file-card-info">
                  <div className="file-card-name">
                    {profile.file_name}
                    {profile.sheet_name !== "Sheet1" && (
                      <span className="file-card-sheet"> / {profile.sheet_name}</span>
                    )}
                  </div>
                  <div className="file-card-meta">
                    {profile.row_count.toLocaleString()} rows
                    <span className="file-card-sep" />
                    {profile.column_count} columns
                  </div>
                </div>
              </div>
            ))}

            {sessionData.warnings.map((w, i) => (
              <div key={`w-${i}`} className="warning-chip">{w}</div>
            ))}
          </div>

          {/* Add file */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            multiple
            style={{ display: "none" }}
            onChange={(e) => handleAddFiles(e.target.files)}
          />
          <button
            className="panel-add-file-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isAddingFile}
          >
            {isAddingFile ? (
              <>
                <span className="panel-add-spinner" />
                Adding...
              </>
            ) : (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Add file
              </>
            )}
          </button>
          {addFileError && (
            <div className="panel-add-error">{addFileError}</div>
          )}
        </div>
      </div>
    </div>
    </div>
  );
}
