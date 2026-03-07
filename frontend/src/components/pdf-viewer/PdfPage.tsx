import { useState } from "react";
import { Page } from "react-pdf";
import { SelectionOverlay } from "./SelectionOverlay";
import type { Selection } from "@/lib/types";

interface PdfPageProps {
  pageNumber: number;
  width: number;
  pageWidthPts: number;
  pageHeightPts: number;
  selections: Selection[];
  onSelectionComplete: (selection: Selection) => void;
  onSelectionRemove: (id: string) => void;
  onSelectionUpdate: (id: string, updates: Partial<Selection>) => void;
}

export function PdfPage({
  pageNumber,
  width,
  pageWidthPts,
  pageHeightPts,
  selections,
  onSelectionComplete,
  onSelectionRemove,
  onSelectionUpdate,
}: PdfPageProps) {
  const scale = width / pageWidthPts;
  const [isRendered, setIsRendered] = useState(false);

  return (
    <div className="relative mb-4 shadow-md" id={`page-${pageNumber}`}>
      <Page
        pageNumber={pageNumber}
        width={width}
        onRenderSuccess={() => setIsRendered(true)}
        renderTextLayer={false}
        renderAnnotationLayer={false}
      />
      {isRendered && (
        <SelectionOverlay
          pageNumber={pageNumber}
          pageWidthPts={pageWidthPts}
          pageHeightPts={pageHeightPts}
          scale={scale}
          selections={selections}
          onSelectionComplete={onSelectionComplete}
          onSelectionRemove={onSelectionRemove}
          onSelectionUpdate={onSelectionUpdate}
        />
      )}
    </div>
  );
}
