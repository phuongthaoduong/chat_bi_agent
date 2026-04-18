import { useState, useEffect, useRef } from "react";

interface LandingPageProps {
  onGetStarted: () => void;
}

type DemoItem =
  | { kind: "user"; text: string }
  | { kind: "answer"; text: string }
  | { kind: "chart"; bars: { label: string; pct: number }[] };

type DemoMsg = DemoItem & { uid: number };

const DEMO_SEQUENCE: DemoItem[] = [
  { kind: "user", text: "Which product sold the most?" },
  { kind: "answer", text: "By product, Hammer leads with 720 units sold." },
  { kind: "user", text: "Show me revenue by region" },
  {
    kind: "chart",
    bars: [
      { label: "East", pct: 100 },
      { label: "West", pct: 77 },
      { label: "South", pct: 59 },
      { label: "North", pct: 44 },
    ],
  },
  { kind: "user", text: "What's the total revenue?" },
  { kind: "answer", text: "Total revenue is $142,800 across all channels." },
];

const APPEAR_AT = [900, 2700, 3600, 5600, 6500, 8300];
const CYCLE_MS = 12000;

export function LandingPage({ onGetStarted }: LandingPageProps) {
  const [demoMsgs, setDemoMsgs] = useState<DemoMsg[]>([]);
  const uidRef = useRef(0);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    const runCycle = () => {
      setDemoMsgs([]);
      DEMO_SEQUENCE.forEach((item, i) => {
        const t = setTimeout(() => {
          setDemoMsgs((prev) => [...prev, { ...item, uid: ++uidRef.current }]);
        }, APPEAR_AT[i]);
        timers.push(t);
      });
      timers.push(setTimeout(runCycle, CYCLE_MS));
    };
    timers.push(setTimeout(runCycle, 600));
    return () => timers.forEach(clearTimeout);
  }, []);

  useEffect(() => {
    const el = messagesContainerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [demoMsgs]);

  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-nav-logo">Chat<em>BI</em></div>
        <button
          className="landing-cta-primary"
          onClick={onGetStarted}
          style={{ padding: "9px 22px", fontSize: "12px" }}
        >
          Get started
        </button>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-glow" />

        <div className="landing-hero-left">
          <h1 className="landing-headline">
            Ask anything<br />about your<br /><em>data.</em>
          </h1>
          <p className="landing-subtext">
            Upload a CSV or Excel file. Ask questions in plain English. Get instant answers and charts.
          </p>
          <button className="landing-cta-primary" onClick={onGetStarted}>
            Upload a file
          </button>
        </div>

        {/* Live demo */}
        <div className="landing-demo">
          <div className="landing-demo-float">
            <div className="demo-panel">
              <div className="demo-panel-stripe" />
              <div className="demo-panel-titlebar">
                <div className="demo-panel-dots">
                  <span className="demo-dot" /><span className="demo-dot" /><span className="demo-dot" />
                </div>
                <span className="demo-panel-filename">sales_data.csv</span>
              </div>
              <div className="demo-messages" ref={messagesContainerRef}>
                {demoMsgs.map((msg) => {
                  if (msg.kind === "user") {
                    return <div key={msg.uid} className="demo-msg-user">{msg.text}</div>;
                  }
                  if (msg.kind === "answer") {
                    return <div key={msg.uid} className="demo-msg-answer">{msg.text}</div>;
                  }
                  if (msg.kind === "chart") {
                    return (
                      <div key={msg.uid} className="demo-msg-chart">
                        <div className="demo-chart-label">Revenue by Region</div>
                        {msg.bars.map((b) => (
                          <div key={b.label} className="demo-bar-row">
                            <span className="demo-bar-lbl">{b.label}</span>
                            <div className="demo-bar-track">
                              <div className="demo-bar-fill" style={{ width: `${b.pct}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
              <div className="demo-input-bar">
                <div className="demo-input-fake">
                  <span className="demo-input-placeholder">Ask a question…</span>
                </div>
                <div className="demo-send-btn">Send →</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3-step strip */}
      <section className="landing-steps">
        {[
          { num: "01", title: "Upload", desc: "Drop in any CSV or Excel file" },
          { num: "02", title: "Ask",    desc: "Type a question in plain English" },
          { num: "03", title: "Discover", desc: "Get answers and charts instantly" },
        ].map((s) => (
          <div key={s.num} className="landing-step">
            <div className="landing-step-num">{s.num}</div>
            <div className="landing-step-title">{s.title}</div>
            <div className="landing-step-desc">{s.desc}</div>
          </div>
        ))}
      </section>

      {/* Footer CTA */}
      <section className="landing-cta-section">
        <div className="landing-cta-glow" />
        <h2 className="landing-cta-title">Ready to talk to your data?</h2>
        <button
          className="landing-cta-primary"
          onClick={onGetStarted}
          style={{ fontSize: "14px", padding: "14px 40px" }}
        >
          Upload a file — it's free
        </button>
      </section>
    </div>
  );
}
