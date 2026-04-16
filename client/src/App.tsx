import { useState } from "react";

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  if (!sessionId) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <p>ChatBI — Upload screen coming next</p>
      </div>
    );
  }

  return <div>Session: {sessionId}</div>;
}

export default App;
