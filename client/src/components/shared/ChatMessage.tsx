import type { Message } from "../../types";
import { ChartCard } from "./ChartCard";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "message--user" : "message--assistant"}`}>
      <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
        {message.content.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
        {message.table && (
          <div className="message-table-wrapper">
            <table className="message-table">
              <thead>
                <tr>
                  {message.table.columns.map((col, i) => (
                    <th key={i}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {message.table.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j}>{cell == null ? "" : String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {message.chart && (
          <div className="message-chart">
            <ChartCard data={message.chart} />
          </div>
        )}
        {message.totalRows != null &&
          message.displayedRows != null &&
          message.totalRows > message.displayedRows && (
            <p className="message-footnote">
              Showing {message.displayedRows.toLocaleString()} of{" "}
              {message.totalRows.toLocaleString()} rows · charts reflect full dataset
            </p>
          )}
      </div>
    </div>
  );
}
