import { useState } from "react";
import type { UploadResponse } from "./types";
import { UploadScreen } from "./components/upload/UploadScreen";
import { SessionScreen } from "./components/session/SessionScreen";

function App() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);

  if (!uploadData) {
    return <UploadScreen onUploadComplete={setUploadData} />;
  }

  return <SessionScreen data={uploadData} onReset={() => setUploadData(null)} />;
}

export default App;
