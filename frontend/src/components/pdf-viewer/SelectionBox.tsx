import { X } from "lucide-react";
import type { Selection } from "@/lib/types";

interface SelectionBoxProps {
  selection: Selection;
  scale: number;
  onRemove: () => void;
  onUpdate: (updates: Partial<Selection>) => void;
}

export function SelectionBox({
  selection,
  scale,
  onRemove,
}: SelectionBoxProps) {
  const style = {
    left: selection.x1 * scale,
    top: selection.y1 * scale,
    width: (selection.x2 - selection.x1) * scale,
    height: (selection.y2 - selection.y1) * scale,
  };

  return (
    <div
      data-selection-box
      className="absolute border-2 border-orange-500 bg-orange-500/15 cursor-move group"
      style={style}
    >
      {/* Close button */}
      <button
        className="absolute -top-3 -right-3 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
      >
        <X className="h-3 w-3" />
      </button>

      {/* Selection label */}
      <span className="absolute -top-5 left-0 text-[10px] bg-orange-500 text-white px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
        Page {selection.page}
      </span>
    </div>
  );
}
