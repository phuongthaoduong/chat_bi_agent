import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import type { ChartData } from "../../types";
import { Chart } from "./Chart";

interface ChartCardProps {
  data: ChartData;
}

export function ChartCard({ data }: ChartCardProps) {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setExpanded(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [expanded]);

  return (
    <>
      <div className="chart-card">
        <div className="chart-card-stripe" />
        <div className="chart-card-body">
          <div className="chart-card-header">
            <div className="chart-card-title">{data.title}</div>
            <button
              className="chart-expand-btn"
              onClick={() => setExpanded(true)}
              title="Expand chart"
            >
              <ExpandIcon />
            </button>
          </div>
          <Chart data={data} />
        </div>
      </div>

      {expanded &&
        createPortal(
          <div
            className="chart-modal-backdrop"
            onClick={() => setExpanded(false)}
          >
            <div
              className="chart-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="chart-modal-header">
                <div className="chart-modal-title">{data.title}</div>
                <button
                  className="chart-modal-close"
                  onClick={() => setExpanded(false)}
                  title="Close"
                >
                  <CloseIcon />
                </button>
              </div>
              <div className="chart-modal-body">
                <Chart data={data} height={480} />
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}

function ExpandIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
