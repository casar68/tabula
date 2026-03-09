import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login, getMe, getAppSettings } from "@/lib/api";
import { saveTokens, useAuthStore } from "@/lib/auth-store";
import { toast } from "sonner";
import { useEffect } from "react";

export function LoginPage() {
  const navigate = useNavigate();
  const { setUser } = useAuthStore();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [allowRegistration, setAllowRegistration] = useState(false);

  useEffect(() => {
    getAppSettings().then((s) => {
      setAllowRegistration(s.allow_registration);
    }).catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const tokens = await login(username, password);
      saveTokens(tokens.access_token, tokens.refresh_token);
      const user = await getMe();
      setUser(user);
      toast.success(`Bienvenue, ${user.username} !`);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur de connexion");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm p-6">
        <div className="text-center mb-6">
          <FileText className="h-10 w-10 text-primary mx-auto mb-2" />
          <h1 className="text-2xl font-bold">Tabula</h1>
          <p className="text-muted-foreground text-sm">Connectez-vous pour continuer</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="username">Nom d'utilisateur</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Mot de passe</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </Button>
        </form>

        {allowRegistration && (
          <p className="text-center text-sm text-muted-foreground mt-4">
            Pas encore de compte ?{" "}
            <Link to="/register" className="text-primary hover:underline">
              Cr\u00e9er un compte
            </Link>
          </p>
        )}
      </Card>
    </div>
  );
}
