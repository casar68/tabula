import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/test-utils";
import { FileUploader } from "../FileUploader";

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock useJobProgress
vi.mock("@/hooks/useJobProgress", () => ({
  useJobProgress: () => ({ data: null }),
}));

// Mock useUploadDocuments
const mockMutateAsync = vi.fn();
vi.mock("@/hooks/useDocuments", () => ({
  useUploadDocuments: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("FileUploader", () => {
  beforeEach(() => {
    mockMutateAsync.mockReset();
    mockNavigate.mockReset();
  });

  it("renders the upload area", () => {
    renderWithProviders(<FileUploader />);
    expect(screen.getByText(/glissez-d/i)).toBeInTheDocument();
    expect(screen.getByText(/parcourir/i)).toBeInTheDocument();
  });

  it("has a hidden file input for PDF files", () => {
    renderWithProviders(<FileUploader />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.accept).toContain("pdf");
    expect(input.multiple).toBe(true);
  });

  it("calls upload when a valid PDF file is selected", async () => {
    mockMutateAsync.mockResolvedValue({
      uploads: [{ id: "doc-1", job_id: "job-1", original_filename: "test.pdf" }],
    });

    renderWithProviders(<FileUploader />);

    const file = new File(["%PDF-1.4 test content"], "test.pdf", {
      type: "application/pdf",
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const user = userEvent.setup();
    await user.upload(input, file);

    expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    const uploadedFiles = mockMutateAsync.mock.calls[0][0];
    expect(uploadedFiles[0].name).toBe("test.pdf");
  });
});
