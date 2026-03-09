import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { DocumentLibrary } from "../DocumentLibrary";
import type { DocumentMeta } from "@/lib/types";

// Mock the useDocuments and useDeleteDocument hooks
const mockDocuments: DocumentMeta[] = [];
const mockMutate = vi.fn();

vi.mock("@/hooks/useDocuments", () => ({
  useDocuments: () => ({
    data: mockDocuments.length > 0 ? mockDocuments : undefined,
    isLoading: false,
  }),
  useDeleteDocument: () => ({
    mutate: mockMutate,
  }),
}));

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("DocumentLibrary", () => {
  beforeEach(() => {
    mockDocuments.length = 0;
    mockNavigate.mockReset();
    mockMutate.mockReset();
  });

  it("renders empty state when no documents", () => {
    renderWithProviders(<DocumentLibrary />);
    expect(screen.getByText(/aucun document/i)).toBeInTheDocument();
  });

  it("renders document list when documents exist", () => {
    mockDocuments.push({
      id: "doc-1",
      original_filename: "report.pdf",
      file_size: 1024 * 512,
      page_count: 5,
      pages: null,
      created_at: "2026-03-01T10:00:00Z",
      updated_at: "2026-03-01T10:00:00Z",
    });

    renderWithProviders(<DocumentLibrary />);
    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("formats file sizes correctly", () => {
    mockDocuments.push({
      id: "doc-1",
      original_filename: "small.pdf",
      file_size: 512,
      page_count: 1,
      pages: null,
      created_at: "2026-03-01T10:00:00Z",
      updated_at: "2026-03-01T10:00:00Z",
    });
    mockDocuments.push({
      id: "doc-2",
      original_filename: "medium.pdf",
      file_size: 1024 * 100,
      page_count: 10,
      pages: null,
      created_at: "2026-03-01T10:00:00Z",
      updated_at: "2026-03-01T10:00:00Z",
    });
    mockDocuments.push({
      id: "doc-3",
      original_filename: "large.pdf",
      file_size: 1024 * 1024 * 2.5,
      page_count: 50,
      pages: null,
      created_at: "2026-03-01T10:00:00Z",
      updated_at: "2026-03-01T10:00:00Z",
    });

    renderWithProviders(<DocumentLibrary />);
    expect(screen.getByText("512 o")).toBeInTheDocument();
    expect(screen.getByText("100.0 Ko")).toBeInTheDocument();
    expect(screen.getByText("2.5 Mo")).toBeInTheDocument();
  });

  it("shows page count or placeholder", () => {
    mockDocuments.push({
      id: "doc-1",
      original_filename: "processing.pdf",
      file_size: 1024,
      page_count: null,
      pages: null,
      created_at: "2026-03-01T10:00:00Z",
      updated_at: "2026-03-01T10:00:00Z",
    });

    renderWithProviders(<DocumentLibrary />);
    expect(screen.getByText("...")).toBeInTheDocument();
  });
});
