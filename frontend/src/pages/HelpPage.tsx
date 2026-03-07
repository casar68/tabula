import { PageLayout } from "@/components/layout/PageLayout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function HelpPage() {
  return (
    <PageLayout title="Aide">
      <div className="max-w-2xl space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Comment utiliser Tabula ?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ol className="list-decimal pl-5 space-y-2">
              <li>
                <strong className="text-foreground">Uploadez un PDF</strong> — Glissez-déposez
                votre fichier PDF ou cliquez sur « Parcourir ».
              </li>
              <li>
                <strong className="text-foreground">Sélectionnez les tableaux</strong> —
                Dessinez des rectangles autour des zones de tableau dans le PDF. Vous
                pouvez aussi cliquer sur « Auto-détecter » pour une détection automatique.
              </li>
              <li>
                <strong className="text-foreground">Extrayez les données</strong> — Cliquez
                sur « Extraire les données » pour prévisualiser les tableaux extraits.
              </li>
              <li>
                <strong className="text-foreground">Exportez</strong> — Téléchargez les
                données en CSV, TSV, JSON ou ZIP. Vous pouvez aussi copier directement
                dans le presse-papiers.
              </li>
            </ol>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Méthodes d'extraction</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ul className="space-y-2">
              <li>
                <strong className="text-foreground">Lattice</strong> — Pour les tableaux
                avec des bordures visibles (lignes horizontales et verticales). Utilise la
                détection de lignes dans le PDF.
              </li>
              <li>
                <strong className="text-foreground">Stream</strong> — Pour les tableaux
                sans bordures, basé sur l'espacement du texte. Adapté aux tableaux
                dont les colonnes sont alignées visuellement.
              </li>
              <li>
                <strong className="text-foreground">Auto</strong> — Détecte automatiquement
                si le tableau utilise des lignes (lattice) ou non (stream).
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">PDF sans texte ?</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <p>
              Tabula ne fonctionne qu'avec des PDF contenant du texte extractible.
              Si votre PDF est un scan (image), il faut d'abord le passer par un
              logiciel OCR (comme Tesseract ou Adobe Acrobat) pour y ajouter une
              couche de texte.
            </p>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}
