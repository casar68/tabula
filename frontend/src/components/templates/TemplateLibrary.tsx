import { useRef } from "react";
import {
  useTemplates,
  useDeleteTemplate,
  useImportTemplate,
} from "@/hooks/useTemplates";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Trash2, Download, Upload, Loader2, LayoutTemplate } from "lucide-react";
import { getTemplateExportUrl } from "@/lib/api";
import { toast } from "sonner";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function TemplateLibrary() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: templates, isLoading } = useTemplates();
  const deleteTemplate = useDeleteTemplate();
  const importTemplate = useImportTemplate();

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await importTemplate.mutateAsync(file);
      toast.success("Template importé");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Erreur d'import"
      );
    }
    e.target.value = "";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => inputRef.current?.click()}
        >
          <Upload className="h-4 w-4 mr-1.5" />
          Importer un template
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={handleImport}
        />
      </div>

      {!templates || templates.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <LayoutTemplate className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>Aucun template sauvegardé.</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead className="w-28">Sélections</TableHead>
              <TableHead className="w-20">Pages</TableHead>
              <TableHead className="w-32">Date</TableHead>
              <TableHead className="w-24" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {templates.map((t) => (
              <TableRow key={t.id}>
                <TableCell className="font-medium">{t.name}</TableCell>
                <TableCell>{t.selection_count}</TableCell>
                <TableCell>{t.page_count}</TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(t.created_at)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <a
                      href={getTemplateExportUrl(t.id)}
                      download
                      className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent"
                    >
                      <Download className="h-4 w-4" />
                    </a>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        if (confirm("Supprimer ce template ?")) {
                          deleteTemplate.mutate(t.id, {
                            onSuccess: () => toast.success("Template supprimé"),
                          });
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
