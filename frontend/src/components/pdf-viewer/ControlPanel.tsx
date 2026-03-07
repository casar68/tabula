import { Button } from "@/components/ui/button";
import { Eraser, Scan, Download } from "lucide-react";
import type { Selection, DetectedTable } from "@/lib/types";

interface ControlPanelProps {
  selections: Selection[];
  detectedTables: DetectedTable[];
  onClearAll: () => void;
  onAutoDetect: () => void;
  onExtract: () => void;
}

export function ControlPanel({
  selections,
  detectedTables,
  onClearAll,
  onAutoDetect,
  onExtract,
}: ControlPanelProps) {
  return (
    <div className="flex items-center gap-2 border-b p-3 bg-muted/30">
      <Button
        variant="outline"
        size="sm"
        onClick={onClearAll}
        disabled={selections.length === 0}
      >
        <Eraser className="h-4 w-4 mr-1.5" />
        Tout effacer
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={onAutoDetect}
        disabled={detectedTables.length === 0}
      >
        <Scan className="h-4 w-4 mr-1.5" />
        Auto-détecter
      </Button>
      <div className="flex-1" />
      <span className="text-sm text-muted-foreground">
        {selections.length} sélection{selections.length !== 1 ? "s" : ""}
      </span>
      <Button size="sm" onClick={onExtract} disabled={selections.length === 0}>
        <Download className="h-4 w-4 mr-1.5" />
        Extraire les données
      </Button>
    </div>
  );
}
