import type { TableResult } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DataPreviewProps {
  tables: TableResult[];
}

export function DataPreview({ tables }: DataPreviewProps) {
  if (tables.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-8">
        Aucune donnée extraite. Essayez une autre méthode ou ajustez votre sélection.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {tables.map((table, idx) => (
        <div key={idx}>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">
            Table {idx + 1} — Page {table.page}
          </h3>
          <div className="border rounded-md overflow-auto max-h-96">
            <Table>
              <TableHeader>
                {table.data.length > 0 && (
                  <TableRow>
                    {table.data[0].map((cell, ci) => (
                      <TableHead key={ci} className="whitespace-nowrap">
                        {cell || <span className="text-muted-foreground/40">—</span>}
                      </TableHead>
                    ))}
                  </TableRow>
                )}
              </TableHeader>
              <TableBody>
                {table.data.slice(1).map((row, ri) => (
                  <TableRow key={ri}>
                    {row.map((cell, ci) => (
                      <TableCell key={ci} className="whitespace-nowrap">
                        {cell || <span className="text-muted-foreground/40">—</span>}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      ))}
    </div>
  );
}
