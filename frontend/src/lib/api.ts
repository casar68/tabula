import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from "./auth-store";
import type {
  AppSettings,
  AuthUser,
  DetectedTable,
  DocumentMeta,
  JobStatus,
  Selection,
  SetupStatus,
  TableResult,
  TemplateMeta,
  TokenPair,
  UploadResult,
} from "./types";

const BASE = "/api";

// ---------------------------------------------------------------------------
// Core request helper with auth
// ---------------------------------------------------------------------------

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res = await fetch(`${BASE}${path}`, { ...options, headers });

  // Handle 401 — try to refresh the token once
  if (res.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      res = await fetch(`${BASE}${path}`, { ...options, headers });
    }
  }

  // Handle 503 setup_required
  if (res.status === 503) {
    const body = await res.json().catch(() => ({}));
    if (body.setup_required) {
      window.location.href = "/setup";
      throw new Error("Setup required");
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const data: TokenPair = await res.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export async function login(
  username: string,
  password: string
): Promise<TokenPair> {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function register(
  username: string,
  password: string
): Promise<AuthUser> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function refreshToken(
  refresh_token: string
): Promise<TokenPair> {
  return request("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token }),
  });
}

export async function getMe(): Promise<AuthUser> {
  return request("/auth/me");
}

// ---------------------------------------------------------------------------
// Setup API
// ---------------------------------------------------------------------------

export async function getSetupStatus(): Promise<SetupStatus> {
  const res = await fetch(`${BASE}/setup/status`);
  return res.json();
}

export async function initSetup(data: {
  mode: "mono" | "multi";
  pg_host?: string;
  pg_port?: number;
  pg_user?: string;
  pg_password?: string;
  pg_database?: string;
  admin_username?: string;
  admin_password?: string;
}): Promise<{ success: boolean; mode: string; message: string }> {
  return request("/setup/init", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Settings API
// ---------------------------------------------------------------------------

export async function getAppSettings(): Promise<AppSettings> {
  const res = await fetch(`${BASE}/settings`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export async function uploadDocuments(
  files: File[]
): Promise<{ uploads: UploadResult[] }> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const headers: Record<string, string> = {};
  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}/documents/upload`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listDocuments(
  offset = 0,
  limit = 50
): Promise<{
  documents: DocumentMeta[];
  total: number;
}> {
  return request(`/documents?offset=${offset}&limit=${limit}`);
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

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return request(`/jobs/${jobId}`);
}

// ---------------------------------------------------------------------------
// Extraction
// ---------------------------------------------------------------------------

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

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(
    `${BASE}/documents/${documentId}/export?${params}`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ selections }),
    }
  );
  if (!res.ok) throw new Error(`Export failed: ${res.statusText}`);
  return res.blob();
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

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

  const headers: Record<string, string> = {};
  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}/templates/import`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Admin API
// ---------------------------------------------------------------------------

export async function listUsers(): Promise<{
  users: AuthUser[];
  total: number;
}> {
  return request("/admin/users");
}

export async function createUser(
  username: string,
  password: string
): Promise<AuthUser> {
  return request("/admin/users", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function deleteUser(userId: string): Promise<void> {
  await request(`/admin/users/${userId}`, { method: "DELETE" });
}

export async function updateAdminSettings(data: {
  allow_registration?: boolean;
}): Promise<{ allow_registration: boolean }> {
  const params = new URLSearchParams();
  if (data.allow_registration !== undefined) {
    params.set("allow_registration", String(data.allow_registration));
  }
  return request(`/admin/settings?${params}`, { method: "PUT" });
}

export async function switchToMulti(data: {
  pg_host: string;
  pg_port: number;
  pg_user: string;
  pg_password: string;
  pg_database: string;
  admin_username: string;
  admin_password: string;
  migrate_data: boolean;
}): Promise<{
  success: boolean;
  mode: string;
  message: string;
  migrated?: { documents: number; templates: number };
}> {
  return request("/admin/switch-to-multi", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function switchToMono(data: {
  source_user_id: string;
  include_all_users: boolean;
}): Promise<{
  success: boolean;
  mode: string;
  message: string;
  migrated?: { documents: number; templates: number };
}> {
  return request("/admin/switch-to-mono", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
