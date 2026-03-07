import { useState } from "react";
import { useParams } from "react-router-dom";
import { useDocument, useDetectedTables } from "@/hooks/useDocuments";
import { useExtractTables } from "@/hooks/useExtraction";
import { useSelectionStore } from "@/lib/store";
import { PdfViewer } from "@/components/pdf-viewer/PdfViewer";
import { DataPreview } from "@/components/extraction/DataPreview";
import { ExportControls } from "@/components/extraction/ExportControls";
import { MethodSelector } from "@/components/extraction/MethodSelector";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft } from "lucide-react";

export function PdfViewPage() {
  const { id } = useParams<{ id: string }>();
  const { data: doc, isLoading: docLoading } = useDocument(id!);
  const { data: tablesData } = useDetectedTables(id!);
  const selections = useSelectionStore((s) => s.selections);
  const extractMutation = useExtractTables(id!);
  const [showResults, setShowResults] = useState(false);

  if (docLoading || !doc) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-3.5rem)]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const handleExtract = async () => {
    if (selections.length === 0) return;
    await extractMutation.mutateAsync(selections);
    setShowResults(true);
  };

  const handleMethodChange = async () => {
    if (selections.length === 0) return;
    await extractMutation.mutateAsync(selections);
  };

  if (showResults && extractMutation.data) {
    return (
      <div className="container mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResults(false)}
          >
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Retour au PDF
          </Button>
          <MethodSelector onMethodChange={handleMethodChange} />
        </div>

        <DataPreview tables={extractMutation.data.tables} />

        <ExportControls
          documentId={doc.id}
          tables={extractMutation.data.tables}
          defaultFilename={doc.original_filename.replace(/\.pdf$/i, "")}
        />
      </div>
    );
  }

  return (
    <PdfViewer
      document={doc}
      detectedTables={tablesData?.tables || []}
      onExtract={handleExtract}
    />
  );
}
