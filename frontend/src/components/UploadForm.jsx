import { useRef, useState } from "react";

export default function UploadForm({ onUpload, disabled }) {
  const [file, setFile] = useState(null);
  const [processingType, setProcessingType] = useState("CSV_ANALYSIS");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const formRef = useRef(null);
  const fileInputRef = useRef(null);

  function chooseFile(nextFile) {
    setFile(nextFile || null);
    setError("");
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) {
      chooseFile(droppedFile);
    }
  }

  function openFilePicker() {
    if (!disabled && !submitting) {
      fileInputRef.current?.click();
    }
  }

  function handleUploadAreaKeyDown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openFilePicker();
    }
  }

  async function submit(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file before uploading.");
      return;
    }
    setError("");
    setProgress(0);
    setSubmitting(true);
    try {
      await onUpload(file, processingType, setProgress);
      setFile(null);
      formRef.current?.reset();
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel upload-panel" aria-labelledby="upload-heading">
      <div className="upload-copy">
        <p className="eyebrow">NEW TASK</p>
        <h2 id="upload-heading">Upload a CSV</h2>
        <p className="muted">Choose a CSV file to create a background analysis task. You can leave this page while it is processed.</p>
      </div>
      <form ref={formRef} onSubmit={submit}>
        <div
          className={`file-input ${isDragging ? "is-dragging" : ""} ${disabled || submitting ? "is-disabled" : ""}`}
          role="button"
          tabIndex={disabled || submitting ? -1 : 0}
          aria-disabled={disabled || submitting}
          aria-label={file ? `Selected CSV file: ${file.name}. Choose another CSV file.` : "Choose a CSV file"}
          onClick={(event) => {
            if (event.target !== fileInputRef.current) {
              openFilePicker();
            }
          }}
          onKeyDown={handleUploadAreaKeyDown}
          onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <span className="file-input-icon" aria-hidden="true">↑</span>
          <span className="file-input-copy">
            <strong>{file ? file.name : "Drop a CSV here or choose a file"}</strong>
            <small>{file ? `${(file.size / 1024).toFixed(1)} KB selected` : "CSV files only"}</small>
          </span>
          <input
            className="native-file-input"
            ref={fileInputRef}
            id="csv-file"
            type="file"
            accept=".csv,text/csv"
            tabIndex={-1}
            onChange={(event) => chooseFile(event.target.files?.[0])}
            disabled={disabled || submitting}
          />
        </div>
        <label className="field-label" htmlFor="processing-type">
          Processing type
          <select
            id="processing-type"
            value={processingType}
            onChange={(event) => setProcessingType(event.target.value)}
            disabled={disabled || submitting}
          >
            <option value="CSV_ANALYSIS">CSV data analysis</option>
          </select>
        </label>
        <button type="submit" disabled={disabled || submitting}>
          {submitting ? `Uploading${progress ? ` ${progress}%` : ""}` : "Create analysis task"}
        </button>
      </form>
      {submitting && <progress value={progress} max="100">{progress}%</progress>}
      {error && <p className="notice error" role="alert">{error}</p>}
    </section>
  );
}
