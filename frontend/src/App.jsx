import { useCallback, useEffect, useState } from "react";

import { downloadReport, listTasks, login, uploadTask } from "./api";
import LoginForm from "./components/LoginForm";
import TaskTable from "./components/TaskTable";
import UploadForm from "./components/UploadForm";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const [token, setToken] = useState(() => window.localStorage.getItem("cloudtask-access-token") || "");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listTasks(token);
      setTasks(response.items);
      setError("");
    } catch (requestError) {
      if (requestError.status === 401) {
        window.localStorage.removeItem("cloudtask-access-token");
        setToken("");
      }
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return undefined;
    }
    refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => window.clearInterval(interval);
  }, [refresh, token]);

  async function handleUpload(file, processingType, onProgress) {
    setUploadMessage("");
    const createdTask = await uploadTask(file, processingType, onProgress, token);
    setTasks((current) => [createdTask, ...current.filter((task) => task.id !== createdTask.id)]);
    await refresh();
    setUploadMessage(`Task created for ${file.name}. Its status will update automatically.`);
  }

  async function handleLogin(email, password) {
    const response = await login(email, password);
    window.localStorage.setItem("cloudtask-access-token", response.access_token);
    setToken(response.access_token);
  }

  async function handleDownload(task) {
    try {
      await downloadReport(task.resultUrl, token);
    } catch (downloadError) {
      setError(downloadError.message);
    }
  }

  if (!token) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <main className="dashboard-shell">
      <header className="app-header">
        <a className="logo" href="/" aria-label="CloudTask dashboard">
          <span className="logo-mark" aria-hidden="true">C</span>
          <span>CloudTask</span>
        </a>
        <a href="/docs" className="docs-link">API documentation <span aria-hidden="true">↗</span></a>
      </header>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">ASYNC CSV ANALYSIS</p>
        <h1 id="page-title">Upload a file. Track the work. Get the report.</h1>
        <p>CloudTask validates your CSV, processes it in the background, and makes the JSON report available when it is ready.</p>
      </section>
      <UploadForm onUpload={handleUpload} disabled={loading && tasks.length === 0} />
      {uploadMessage && <p className="notice success" role="status">{uploadMessage}</p>}
      <TaskTable tasks={tasks} loading={loading} error={error} onRefresh={refresh} onDownload={handleDownload} />
    </main>
  );
}
