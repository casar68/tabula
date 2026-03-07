import { useCallback, useRef, useState } from "react";
import type { Selection } from "@/lib/types";

interface UseRectangularSelectionOptions {
  pageNumber: number;
  pageWidthPts: number;
  pageHeightPts: number;
  scale: number;
  existingSelections: Selection[];
  onSelectionComplete: (selection: Selection) => void;
}

export function useRectangularSelection({
  pageNumber,
  pageWidthPts,
  pageHeightPts,
  scale,
  existingSelections: _existingSelections,
  onSelectionComplete,
}: UseRectangularSelectionOptions) {
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawRect, setDrawRect] = useState<{
    x: number;
    y: number;
    w: number;
    h: number;
  } | null>(null);
  const startRef = useRef<{ x: number; y: number } | null>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      // Only start on left click, not on existing selections
      if (e.button !== 0) return;
      const target = e.target as HTMLElement;
      if (target.closest("[data-selection-box]")) return;

      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      startRef.current = { x, y };
      setIsDrawing(true);
      setDrawRect({ x, y, w: 0, h: 0 });
    },
    []
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!isDrawing || !startRef.current) return;

      const rect = e.currentTarget.getBoundingClientRect();
      const currentX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const currentY = Math.max(
        0,
        Math.min(e.clientY - rect.top, rect.height)
      );

      const x = Math.min(startRef.current.x, currentX);
      const y = Math.min(startRef.current.y, currentY);
      const w = Math.abs(currentX - startRef.current.x);
      const h = Math.abs(currentY - startRef.current.y);

      setDrawRect({ x, y, w, h });
    },
    [isDrawing]
  );

  const handleMouseUp = useCallback(() => {
    if (!isDrawing || !drawRect) {
      setIsDrawing(false);
      setDrawRect(null);
      return;
    }

    // Minimum size check (at least 1% of page)
    const minSize = Math.min(pageWidthPts, pageHeightPts) * scale * 0.01;
    if (drawRect.w < minSize || drawRect.h < minSize) {
      setIsDrawing(false);
      setDrawRect(null);
      return;
    }

    // Convert pixel coords to PDF points
    const sel: Selection = {
      id: crypto.randomUUID(),
      page: pageNumber,
      x1: drawRect.x / scale,
      y1: drawRect.y / scale,
      x2: (drawRect.x + drawRect.w) / scale,
      y2: (drawRect.y + drawRect.h) / scale,
      width: drawRect.w / scale,
      height: drawRect.h / scale,
      extraction_method: "guess",
    };

    onSelectionComplete(sel);
    setIsDrawing(false);
    setDrawRect(null);
    startRef.current = null;
  }, [
    isDrawing,
    drawRect,
    pageNumber,
    pageWidthPts,
    pageHeightPts,
    scale,
    onSelectionComplete,
  ]);

  return {
    isDrawing,
    drawRect,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
  };
}
