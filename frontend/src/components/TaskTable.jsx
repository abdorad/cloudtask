const labels = {
  PENDING: "Queued",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  FAILED: "Failed"
};

const processingLabels = {
  CSV_ANALYSIS: "CSV data analysis"
};

function formatDate(value) {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export default function TaskTable({ tasks, loading, error, onRefresh, onDownload }) {
  return (
    <section className="panel task-panel" aria-labelledby="tasks-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">TASK DASHBOARD</p>
          <h2 id="tasks-heading">Your processing tasks</h2>
          <p className="muted section-description">Task statuses refresh automatically every five seconds.</p>
        </div>
        <button className="secondary" type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>
      {error && <p className="notice error" role="alert">Unable to refresh tasks. {error}</p>}
      {loading && tasks.length === 0 && <p className="empty" role="status">Loading your tasks…</p>}
      {!loading && !error && tasks.length === 0 && (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">↑</span>
          <h3>No processing tasks yet</h3>
          <p>Upload a CSV above to create your first analysis task.</p>
        </div>
      )}
      {tasks.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Processing type</th>
                <th>Status</th>
                <th>Submitted</th>
                <th className="align-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td data-label="File">
                    <strong>{task.originalFilename}</strong>
                    <small>{(task.sizeBytes / 1024).toFixed(1)} KB</small>
                    {task.error && <small className="failure-detail">{task.error}</small>}
                  </td>
                  <td data-label="Processing type">{processingLabels[task.processingType] || task.processingType}</td>
                  <td data-label="Status"><span className={`status ${task.status.toLowerCase()}`}>{labels[task.status] || task.status}</span></td>
                  <td data-label="Submitted">{formatDate(task.createdAt)}</td>
                  <td className="task-action" data-label="Actions">
                    {task.resultAvailable ? <button className="secondary report-link" type="button" onClick={() => onDownload(task)}>Download JSON</button> : <span className="unavailable">Report pending</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
