import { useMutation } from "@tanstack/react-query";
import * as api from "@/lib/api";
import type { Selection } from "@/lib/types";

function selectionsToApiFormat(selections: Selection[]) {
  return selections.map((s) => ({
    page: s.page,
    x1: s.x1,
    y1: s.y1,
    x2: s.x2,
    y2: s.y2,
    extraction_method: s.extraction_method,
  }));
}

export function useExtractTables(documentId: string) {
  return useMutation({
    mutationFn: (selections: Selection[]) =>
      api.extractTables(documentId, selectionsToApiFormat(selections)),
  });
}

export function useExportTables(documentId: string) {
  return useMutation({
    mutationFn: async ({
      selections,
      format,
      filename,
    }: {
      selections: Selection[];
      format: string;
      filename?: string;
    }) => {
      const blob = await api.exportTables(
        documentId,
        selectionsToApiFormat(selections),
        format,
        filename
      );
      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `tabula-export.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });
}
