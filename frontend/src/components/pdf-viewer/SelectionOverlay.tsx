import type { Selection } from "@/lib/types";
import { SelectionBox } from "./SelectionBox";
import { useRectangularSelection } from "@/hooks/useRectangularSelection";

interface SelectionOverlayProps {
  pageNumber: number;
  pageWidthPts: number;
  pageHeightPts: number;
  scale: number;
  selections: Selection[];
  onSelectionComplete: (selection: Selection) => void;
  onSelectionRemove: (id: string) => void;
  onSelectionUpdate: (id: string, updates: Partial<Selection>) => void;
}

export function SelectionOverlay({
  pageNumber,
  pageWidthPts,
  pageHeightPts,
  scale,
  selections,
  onSelectionComplete,
  onSelectionRemove,
  onSelectionUpdate,
}: SelectionOverlayProps) {
  const { isDrawing, drawRect, handleMouseDown, handleMouseMove, handleMouseUp } =
    useRectangularSelection({
      pageNumber,
      pageWidthPts,
      pageHeightPts,
      scale,
      existingSelections: selections,
      onSelectionComplete,
    });

  const pageSelections = selections.filter((s) => s.page === pageNumber);

  return (
    <div
      className="absolute inset-0"
      style={{ cursor: isDrawing ? "crosshair" : "crosshair" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Existing selections */}
      {pageSelections.map((sel) => (
        <SelectionBox
          key={sel.id}
          selection={sel}
          scale={scale}
          onRemove={() => onSelectionRemove(sel.id)}
          onUpdate={(updates) => onSelectionUpdate(sel.id, updates)}
        />
      ))}

      {/* Active drawing rectangle */}
      {isDrawing && drawRect && drawRect.w > 0 && drawRect.h > 0 && (
        <div
          className="absolute border-2 border-dashed border-orange-500 bg-orange-500/10 pointer-events-none"
          style={{
            left: drawRect.x,
            top: drawRect.y,
            width: drawRect.w,
            height: drawRect.h,
          }}
        />
      )}
    </div>
  );
}
