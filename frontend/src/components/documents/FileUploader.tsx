import { useCallback, useRef, useState } from "react";
import { Upload, FileWarning } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadDocuments } from "@/hooks/useDocuments";
import { useJobProgress } from "@/hooks/useJobProgress";
import { Progress } from "@/components/ui/progress";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

export function FileUploader() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploadedDocId, setUploadedDocId] = useState<string | null>(null);
  const upload = useUploadDocuments();

  const { data: jobStatus } = useJobProgress(jobId);

  // Navigate when job completes
  if (jobStatus?.status === "completed" && uploadedDocId) {
    setJobId(null);
    setUploadedDocId(null);
    navigate(`/pdf/${uploadedDocId}`);
  }

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const pdfFiles = Array.from(files).filter(
        (f) => f.type === "application/pdf" || f.name.endsWith(".pdf")
      );

      if (pdfFiles.length === 0) {
        toast.error("Veuillez sélectionner des fichiers PDF.");
        return;
      }

      try {
        const result = await upload.mutateAsync(pdfFiles);
        if (result.uploads.length > 0) {
          const first = result.uploads[0];
          setUploadedDocId(first.id);
          setJobId(first.job_id);
          toast.success(
            `${pdfFiles.length} fichier(s) uploadé(s). Traitement en cours...`
          );
        }
      } catch (err) {
        toast.error(
          err instanceof Error ? err.message : "Erreur lors de l'upload"
        );
      }
    },
    [upload, navigate]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
      >
        <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
        <p className="text-sm text-muted-foreground mb-3">
          Glissez-déposez vos fichiers PDF ici, ou
        </p>
        <Button
          variant="outline"
          onClick={() => inputRef.current?.click()}
          disabled={upload.isPending}
        >
          Parcourir
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {jobId && jobStatus && jobStatus.status !== "completed" && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {jobStatus.message || "Traitement en cours..."}
            </span>
            <span className="font-medium">{jobStatus.progress}%</span>
          </div>
          <Progress value={jobStatus.progress} />
          {jobStatus.status === "failed" && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <FileWarning className="h-4 w-4" />
              {jobStatus.error_type === "no-text"
                ? "Ce PDF ne contient pas de texte extractible (PDF image ?)."
                : jobStatus.message || "Erreur de traitement."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
