import { useDocuments, useDeleteDocument } from "@/hooks/useDocuments";
import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Trash2, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DocumentLibrary() {
  const navigate = useNavigate();
  const { data: documents, isLoading } = useDocuments();
  const deleteDoc = useDeleteDocument();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>Aucun document. Uploadez un PDF pour commencer.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nom</TableHead>
          <TableHead className="w-24">Taille</TableHead>
          <TableHead className="w-20">Pages</TableHead>
          <TableHead className="w-40">Date</TableHead>
          <TableHead className="w-20" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow
            key={doc.id}
            className="cursor-pointer"
            onClick={() => navigate(`/pdf/${doc.id}`)}
          >
            <TableCell className="font-medium">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                {doc.original_filename}
              </div>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatFileSize(doc.file_size)}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {doc.page_count ?? "..."}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatDate(doc.created_at)}
            </TableCell>
            <TableCell>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("Supprimer ce document ?")) {
                    deleteDoc.mutate(doc.id, {
                      onSuccess: () => toast.success("Document supprimé"),
                    });
                  }
                }}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
