export interface PageInfo {
  number: number;
  width: number;
  height: number;
  rotation: number;
}

export interface DocumentMeta {
  id: string;
  original_filename: string;
  file_size: number;
  page_count: number | null;
  pages: PageInfo[] | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResult {
  id: string;
  job_id: string;
  original_filename: string;
}

export interface JobStatus {
  id: string;
  document_id: string;
  status: "queued" | "working" | "completed" | "failed";
  progress: number;
  message: string | null;
  error_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface Selection {
  id: string;
  page: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
  extraction_method: "guess" | "stream" | "lattice";
}

export interface DetectedTable {
  page: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface TableResult {
  spec_index: number;
  page: number;
  data: string[][];
}

export interface TemplateMeta {
  id: string;
  name: string;
  selections: Selection[];
  selection_count: number;
  page_count: number;
  created_at: string;
  updated_at: string;
}
