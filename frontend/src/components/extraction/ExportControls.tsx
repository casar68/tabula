import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download, Copy, Loader2 } from "lucide-react";
import { useExportTables } from "@/hooks/useExtraction";
import { useSelectionStore } from "@/lib/store";
import type { TableResult } from "@/lib/types";
import { toast } from "sonner";

const FORMATS = [
  { value: "csv", label: "CSV" },
  { value: "tsv", label: "TSV" },
  { value: "json", label: "JSON" },
  { value: "zip", label: "ZIP" },
] as const;

interface ExportControlsProps {
  documentId: string;
  tables: TableResult[];
  defaultFilename: string;
}

export function ExportControls({
  documentId,
  tables,
  defaultFilename,
}: ExportControlsProps) {
  const [format, setFormat] = useState<string>("csv");
  const [filename, setFilename] = useState(defaultFilename);
  const exportMutation = useExportTables(documentId);
  const selections = useSelectionStore((s) => s.selections);

  const handleExport = () => {
    exportMutation.mutate({
      selections,
      format,
      filename,
    });
  };

  const handleCopy = async () => {
    const text = tables
      .map((t) => t.data.map((row) => row.join("\t")).join("\n"))
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copié dans le presse-papiers");
    } catch {
      toast.error("Impossible de copier");
    }
  };

  return (
    <div className="flex items-center gap-3 border-t pt-4">
      <Input
        value={filename}
        onChange={(e) => setFilename(e.target.value)}
        className="w-48"
        placeholder="Nom du fichier"
      />

      <div className="flex items-center border rounded-md">
        {FORMATS.map((f) => (
          <button
            key={f.value}
            className={`px-3 py-1.5 text-sm transition-colors ${
              format === f.value
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
            onClick={() => setFormat(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <Button onClick={handleExport} disabled={exportMutation.isPending}>
        {exportMutation.isPending ? (
          <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
        ) : (
          <Download className="h-4 w-4 mr-1.5" />
        )}
        Télécharger
      </Button>

      <Button variant="outline" onClick={handleCopy}>
        <Copy className="h-4 w-4 mr-1.5" />
        Copier
      </Button>
    </div>
  );
}
