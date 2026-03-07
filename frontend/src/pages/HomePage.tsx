import { PageLayout } from "@/components/layout/PageLayout";
import { FileUploader } from "@/components/documents/FileUploader";
import { DocumentLibrary } from "@/components/documents/DocumentLibrary";
import { Separator } from "@/components/ui/separator";

export function HomePage() {
  return (
    <PageLayout title="Mes fichiers">
      <FileUploader />
      <Separator className="my-6" />
      <DocumentLibrary />
    </PageLayout>
  );
}
