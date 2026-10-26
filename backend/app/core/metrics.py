from prometheus_client import Counter, Histogram

API_REQUESTS = Counter(
    "cloudtask_api_requests_total",
    "HTTP requests handled by the API",
    ["method", "path", "status"],
)
API_DURATION = Histogram(
    "cloudtask_api_request_duration_seconds",
    "Duration of API HTTP requests",
    ["method", "path"],
)
TASKS_CREATED = Counter("cloudtask_tasks_created_total", "Tasks accepted by the API")
TASK_OUTCOMES = Counter(
    "cloudtask_task_outcomes_total",
    "Worker task outcomes",
    ["outcome"],
)
TASK_DURATION = Histogram(
    "cloudtask_task_processing_duration_seconds",
    "CSV worker processing duration",
)
