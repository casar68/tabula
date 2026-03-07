import { useCallback, useState } from "react";
import { Document } from "react-pdf";
import { PdfPage } from "./PdfPage";
import { ThumbnailSidebar } from "./ThumbnailSidebar";
import { ControlPanel } from "./ControlPanel";
import { Loader2 } from "lucide-react";
import { useSelectionStore } from "@/lib/store";
import { getDocumentFileUrl } from "@/lib/api";
import type { DocumentMeta, DetectedTable, Selection } from "@/lib/types";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

interface PdfViewerProps {
  document: DocumentMeta;
  detectedTables: DetectedTable[];
  onExtract: () => void;
}

const PAGE_WIDTH = 700;

export function PdfViewer({
  document: doc,
  detectedTables,
  onExtract,
}: PdfViewerProps) {
  const [activePage, setActivePage] = useState(1);
  const {
    selections,
    addSelection,
    removeSelection,
    updateSelection,
    clearSelections,
    setSelections,
  } = useSelectionStore();

  const handlePageClick = useCallback((pageNumber: number) => {
    setActivePage(pageNumber);
    const el = document.getElementById(`page-${pageNumber}`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleAutoDetect = useCallback(() => {
    const newSelections: Selection[] = detectedTables.map((t) => ({
      id: crypto.randomUUID(),
      page: t.page,
      x1: t.x1,
      y1: t.y1,
      x2: t.x2,
      y2: t.y2,
      width: t.width,
      height: t.height,
      extraction_method: "guess" as const,
    }));
    setSelections(newSelections);
  }, [detectedTables, setSelections]);

  const pages = doc.pages || [];
  const fileUrl = getDocumentFileUrl(doc.id);

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <ControlPanel
        selections={selections}
        detectedTables={detectedTables}
        onClearAll={clearSelections}
        onAutoDetect={handleAutoDetect}
        onExtract={onExtract}
      />
      <div className="flex flex-1 overflow-hidden">
        <Document
          file={fileUrl}
          loading={
            <div className="flex items-center justify-center flex-1 py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          }
        >
          {/* Thumbnail sidebar */}
          {pages.length > 0 && (
            <ThumbnailSidebar
              pages={pages}
              selections={selections}
              activePage={activePage}
              onPageClick={handlePageClick}
            />
          )}

          {/* Main page area */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col items-center">
            {pages.map((page) => (
              <PdfPage
                key={page.number}
                pageNumber={page.number}
                width={PAGE_WIDTH}
                pageWidthPts={page.width}
                pageHeightPts={page.height}
                selections={selections}
                onSelectionComplete={addSelection}
                onSelectionRemove={removeSelection}
                onSelectionUpdate={updateSelection}
              />
            ))}
          </div>
        </Document>
      </div>
    </div>
  );
}
