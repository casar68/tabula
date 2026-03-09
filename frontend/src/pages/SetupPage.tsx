import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Database, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { initSetup } from "@/lib/api";
import { toast } from "sonner";

type Step = "choose" | "config-multi" | "done";

export function SetupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("choose");
  const [loading, setLoading] = useState(false);
  const [pgForm, setPgForm] = useState({
    pg_host: "localhost",
    pg_port: "5432",
    pg_user: "postgres",
    pg_password: "",
    pg_database: "tabula",
    admin_username: "admin",
    admin_password: "",
  });

  async function handleMono() {
    setLoading(true);
    try {
      await initSetup({ mode: "mono" });
      toast.success("Mode mono-utilisateur activ\u00e9");
      navigate("/", { replace: true });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  async function handleMultiSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await initSetup({
        mode: "multi",
        pg_host: pgForm.pg_host,
        pg_port: parseInt(pgForm.pg_port),
        pg_user: pgForm.pg_user,
        pg_password: pgForm.pg_password,
        pg_database: pgForm.pg_database,
        admin_username: pgForm.admin_username,
        admin_password: pgForm.admin_password,
      });
      toast.success("Mode multi-utilisateurs activ\u00e9");
      navigate("/login", { replace: true });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  if (step === "config-multi") {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-lg p-6">
          <h1 className="text-2xl font-bold mb-1">Configuration multi-utilisateurs</h1>
          <p className="text-muted-foreground mb-6 text-sm">
            Renseignez la connexion PostgreSQL et cr\u00e9ez le compte administrateur.
          </p>

          <form onSubmit={handleMultiSubmit} className="space-y-4">
            <fieldset className="space-y-3">
              <legend className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Database className="h-4 w-4" /> PostgreSQL
              </legend>
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <Label htmlFor="pg_host">H\u00f4te</Label>
                  <Input
                    id="pg_host"
                    value={pgForm.pg_host}
                    onChange={(e) => setPgForm({ ...pgForm, pg_host: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="pg_port">Port</Label>
                  <Input
                    id="pg_port"
                    value={pgForm.pg_port}
                    onChange={(e) => setPgForm({ ...pgForm, pg_port: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="pg_user">Utilisateur</Label>
                  <Input
                    id="pg_user"
                    value={pgForm.pg_user}
                    onChange={(e) => setPgForm({ ...pgForm, pg_user: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="pg_password">Mot de passe</Label>
                  <Input
                    id="pg_password"
                    type="password"
                    value={pgForm.pg_password}
                    onChange={(e) => setPgForm({ ...pgForm, pg_password: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="pg_database">Base de donn\u00e9es</Label>
                <Input
                  id="pg_database"
                  value={pgForm.pg_database}
                  onChange={(e) => setPgForm({ ...pgForm, pg_database: e.target.value })}
                  required
                />
              </div>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Users className="h-4 w-4" /> Administrateur
              </legend>
              <div>
                <Label htmlFor="admin_username">Nom d'utilisateur</Label>
                <Input
                  id="admin_username"
                  value={pgForm.admin_username}
                  onChange={(e) => setPgForm({ ...pgForm, admin_username: e.target.value })}
                  minLength={3}
                  required
                />
              </div>
              <div>
                <Label htmlFor="admin_password">Mot de passe</Label>
                <Input
                  id="admin_password"
                  type="password"
                  value={pgForm.admin_password}
                  onChange={(e) => setPgForm({ ...pgForm, admin_password: e.target.value })}
                  minLength={6}
                  required
                />
              </div>
            </fieldset>

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep("choose")}
                disabled={loading}
              >
                Retour
              </Button>
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? "Configuration..." : "Valider"}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    );
  }

  // Step: choose mode
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <FileText className="h-12 w-12 text-primary mx-auto mb-3" />
          <h1 className="text-3xl font-bold">Bienvenue sur Tabula</h1>
          <p className="text-muted-foreground mt-2">
            Choisissez le mode de fonctionnement de l'application.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <Card
            className="p-6 cursor-pointer hover:border-primary transition-colors"
            onClick={handleMono}
          >
            <Database className="h-8 w-8 text-primary mb-3" />
            <h2 className="text-lg font-semibold mb-2">Mono-utilisateur</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Base SQLite locale. Aucune authentification. Id\u00e9al pour un usage personnel.
            </p>
            <Button
              variant="outline"
              className="w-full"
              disabled={loading}
              onClick={(e) => {
                e.stopPropagation();
                handleMono();
              }}
            >
              {loading ? "Installation..." : "Choisir ce mode"}
            </Button>
          </Card>

          <Card
            className="p-6 cursor-pointer hover:border-primary transition-colors"
            onClick={() => setStep("config-multi")}
          >
            <Users className="h-8 w-8 text-primary mb-3" />
            <h2 className="text-lg font-semibold mb-2">Multi-utilisateurs</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Base PostgreSQL. Comptes utilisateurs avec authentification. Pour les \u00e9quipes.
            </p>
            <Button
              variant="outline"
              className="w-full"
              onClick={(e) => {
                e.stopPropagation();
                setStep("config-multi");
              }}
            >
              Configurer
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
