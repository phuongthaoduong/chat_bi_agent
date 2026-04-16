import { useState } from "react";
import { UploadResponse } from "./types";
import { UploadScreen } from "./components/upload/UploadScreen";

function App() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);

  if (!uploadData) {
    return <UploadScreen onUploadComplete={setUploadData} />;
  }

  return (
    <div style={{ padding: "24px" }}>
      <h2>Session: {uploadData.session_id}</h2>
      <pre>{JSON.stringify(uploadData, null, 2)}</pre>
    </div>
  );
}

export default App;
