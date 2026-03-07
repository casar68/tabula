import type {
  DocumentMeta,
  DetectedTable,
  JobStatus,
  Selection,
  TableResult,
  TemplateMeta,
  UploadResult,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Documents
export async function uploadDocuments(
  files: File[]
): Promise<{ uploads: UploadResult[] }> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const res = await fetch(`${BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listDocuments(): Promise<{
  documents: DocumentMeta[];
}> {
  return request("/documents");
}

export async function getDocument(id: string): Promise<DocumentMeta> {
  return request(`/documents/${id}`);
}

export async function deleteDocument(id: string): Promise<void> {
  await request(`/documents/${id}`, { method: "DELETE" });
}

export function getDocumentFileUrl(id: string): string {
  return `${BASE}/documents/${id}/file`;
}

export async function getDetectedTables(
  id: string
): Promise<{ tables: DetectedTable[] }> {
  return request(`/documents/${id}/tables`);
}

// Jobs
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return request(`/jobs/${jobId}`);
}

// Extraction
export async function extractTables(
  documentId: string,
  selections: Omit<Selection, "id" | "width" | "height">[]
): Promise<{ tables: TableResult[] }> {
  return request(`/documents/${documentId}/extract`, {
    method: "POST",
    body: JSON.stringify({ selections }),
  });
}

export function getExportUrl(
  documentId: string,
  format: "csv" | "tsv" | "json" | "zip"
): string {
  return `${BASE}/documents/${documentId}/export?format=${format}`;
}

export async function exportTables(
  documentId: string,
  selections: Omit<Selection, "id" | "width" | "height">[],
  format: string,
  filename?: string
): Promise<Blob> {
  const params = new URLSearchParams({ format });
  if (filename) params.set("filename", filename);
  const res = await fetch(
    `${BASE}/documents/${documentId}/export?${params}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selections }),
    }
  );
  if (!res.ok) throw new Error(`Export failed: ${res.statusText}`);
  return res.blob();
}

// Templates
export async function listTemplates(): Promise<{
  templates: TemplateMeta[];
}> {
  return request("/templates");
}

export async function createTemplate(data: {
  name: string;
  selections: Selection[];
  page_count: number;
}): Promise<TemplateMeta> {
  return request("/templates", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTemplate(id: string): Promise<TemplateMeta> {
  return request(`/templates/${id}`);
}

export async function updateTemplate(
  id: string,
  data: { name?: string }
): Promise<TemplateMeta> {
  return request(`/templates/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteTemplate(id: string): Promise<void> {
  await request(`/templates/${id}`, { method: "DELETE" });
}

export function getTemplateExportUrl(id: string): string {
  return `${BASE}/templates/${id}/export`;
}

export async function importTemplate(file: File): Promise<TemplateMeta> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/templates/import`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
