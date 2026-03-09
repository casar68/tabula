import { PageLayout } from "@/components/layout/PageLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function AboutPage() {
  return (
    <PageLayout title="À propos">
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Tabula</CardTitle>
          <CardDescription>
            Extraction de tableaux depuis des fichiers PDF
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>
            Tabula est un outil qui permet d'extraire les données tabulaires
            piégées dans des fichiers PDF. Sélectionnez visuellement les zones
            de tableau, choisissez votre méthode d'extraction, et exportez les
            données en CSV, TSV, JSON ou ZIP.
          </p>
          <p>
            Basé sur le projet open source Tabula, cette version a été
            entièrement réécrite avec Python (FastAPI + PyMuPDF) et
            React (TypeScript + Vite).
          </p>
          <div className="pt-2">
            <h4 className="font-medium text-foreground mb-1">Stack technique</h4>
            <ul className="list-disc pl-5 space-y-0.5">
              <li>Backend : FastAPI + SQLAlchemy + PyMuPDF</li>
              <li>Frontend : React 19 + TypeScript + Tailwind CSS</li>
              <li>Rendu PDF : react-pdf (pdf.js côté navigateur)</li>
              <li>Base de données : PostgreSQL</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </PageLayout>
  );
}
