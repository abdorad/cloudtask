import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import TaskTable from "./TaskTable";

describe("TaskTable", () => {
  it("shows a completed task and its report link", () => {
    render(
      <TaskTable
        loading={false}
        error=""
        onRefresh={vi.fn()}
        onDownload={vi.fn()}
        tasks={[{
          id: "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1",
          originalFilename: "customers.csv",
          status: "COMPLETED",
          sizeBytes: 1024,
          attemptCount: 1,
          createdAt: "2026-10-22T12:00:00Z",
          resultAvailable: true,
          resultUrl: "/api/v1/tasks/c508c8af-2aec-4358-8cd5-2bf81c9c0cf1/result"
        }]}
      />
    );

    expect(screen.getByText("customers.csv")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download JSON" })).toBeInTheDocument();
  });
});
