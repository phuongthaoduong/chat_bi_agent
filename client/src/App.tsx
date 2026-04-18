import { useState } from "react";
import type { UploadResponse } from "./types";
import { LandingPage } from "./components/landing/LandingPage";
import { UploadScreen } from "./components/upload/UploadScreen";
import { SessionScreen } from "./components/session/SessionScreen";

type View = "landing" | "upload" | "session";

function App() {
  const [view, setView] = useState<View>("landing");
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);

  if (view === "landing") {
    return <LandingPage onGetStarted={() => setView("upload")} />;
  }

  if (view === "upload" || !uploadData) {
    return (
      <UploadScreen
        onUploadComplete={(data) => {
          setUploadData(data);
          setView("session");
        }}
      />
    );
  }

  return (
    <SessionScreen
      data={uploadData}
      onReset={() => {
        setUploadData(null);
        setView("landing");
      }}
    />
  );
}

export default App;
