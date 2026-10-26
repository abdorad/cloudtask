const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function readJson(response) {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(body?.message || "The request could not be completed.");
    error.status = response.status;
    throw error;
  }
  return body;
}

function authorization(token) {
  return { Authorization: `Bearer ${token}` };
}

export async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return readJson(response);
}

export async function listTasks(token) {
  const response = await fetch(`${API_BASE_URL}/tasks`, { headers: authorization(token) });
  return readJson(response);
}

export async function downloadReport(url, token) {
  const response = await fetch(url, { headers: authorization(token) });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message || "The report could not be downloaded.");
  }
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = "cloudtask-report.json";
  link.click();
  window.URL.revokeObjectURL(downloadUrl);
}

export function uploadTask(file, processingType, onProgress, token) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("processingType", processingType);

    request.open("POST", `${API_BASE_URL}/tasks`);
    request.setRequestHeader("Authorization", `Bearer ${token}`);
    request.responseType = "json";
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });
    request.addEventListener("load", () => {
      const body = request.response;
      if (request.status >= 200 && request.status < 300) {
        resolve(body);
      } else {
        reject(new Error(body?.message || "The upload could not be completed."));
      }
    });
    request.addEventListener("error", () => reject(new Error("The API could not be reached.")));
    request.send(formData);
  });
}
