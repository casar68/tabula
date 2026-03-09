import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Database,
  Users,
  UserPlus,
  Trash2,
  RefreshCw,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getAppSettings,
  listUsers,
  createUser,
  deleteUser,
  updateAdminSettings,
  switchToMulti,
  switchToMono,
} from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { AppSettings, AuthUser } from "@/lib/types";
import { toast } from "sonner";

export function SettingsPage() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuthStore();
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [showModeSwitchDialog, setShowModeSwitchDialog] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // Mode switch state (mono -> multi)
  const [pgForm, setPgForm] = useState({
    pg_host: "localhost",
    pg_port: "5432",
    pg_user: "postgres",
    pg_password: "",
    pg_database: "tabula",
    admin_username: "admin",
    admin_password: "",
    migrate_data: true,
  });

  // Mode switch state (multi -> mono)
  const [selectedUserId, setSelectedUserId] = useState("");
  const [includeAll, setIncludeAll] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const s = await getAppSettings();
      setSettings(s);
      if (s.mode === "multi" && currentUser?.is_admin) {
        const { users: u } = await listUsers();
        setUsers(u);
      }
    } catch {
      toast.error("Impossible de charger les param\u00e8tres");
    }
  }

  async function handleToggleRegistration() {
    if (!settings) return;
    try {
      const result = await updateAdminSettings({
        allow_registration: !settings.allow_registration,
      });
      setSettings({ ...settings, allow_registration: result.allow_registration });
      toast.success(
        result.allow_registration
          ? "Inscription activ\u00e9e"
          : "Inscription d\u00e9sactiv\u00e9e"
      );
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleCreateUser(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createUser(newUsername, newPassword);
      toast.success(`Utilisateur "${newUsername}" cr\u00e9\u00e9`);
      setNewUsername("");
      setNewPassword("");
      setShowCreateUser(false);
      loadSettings();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleDeleteUser(userId: string, username: string) {
    if (!confirm(`Supprimer l'utilisateur "${username}" ?`)) return;
    try {
      await deleteUser(userId);
      toast.success(`Utilisateur "${username}" supprim\u00e9`);
      loadSettings();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function handleSwitchToMulti(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await switchToMulti({
        pg_host: pgForm.pg_host,
        pg_port: parseInt(pgForm.pg_port),
        pg_user: pgForm.pg_user,
        pg_password: pgForm.pg_password,
        pg_database: pgForm.pg_database,
        admin_username: pgForm.admin_username,
        admin_password: pgForm.admin_password,
        migrate_data: pgForm.migrate_data,
      });
      toast.success(result.message);
      if (result.migrated) {
        toast.info(
          `${result.migrated.documents} document(s) et ${result.migrated.templates} template(s) migr\u00e9(s)`
        );
      }
      navigate("/login", { replace: true });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  async function handleSwitchToMono(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUserId) {
      toast.error("S\u00e9lectionnez un utilisateur");
      return;
    }
    setLoading(true);
    try {
      const result = await switchToMono({
        source_user_id: selectedUserId,
        include_all_users: includeAll,
      });
      toast.success(result.message);
      if (result.migrated) {
        toast.info(
          `${result.migrated.documents} document(s) et ${result.migrated.templates} template(s) migr\u00e9(s)`
        );
      }
      navigate("/", { replace: true });
      window.location.reload();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  if (!settings) {
    return (
      <div className="container mx-auto p-6">
        <p className="text-muted-foreground">Chargement...</p>
      </div>
    );
  }

  const isAdmin = !currentUser || currentUser.is_admin;

  return (
    <div className="container mx-auto p-6 max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Param\u00e8tres</h1>

      {/* Current mode */}
      <Card className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {settings.mode === "mono" ? (
              <Database className="h-5 w-5 text-primary" />
            ) : (
              <Users className="h-5 w-5 text-primary" />
            )}
            <div>
              <p className="font-medium">
                Mode : {settings.mode === "mono" ? "Mono-utilisateur" : "Multi-utilisateurs"}
              </p>
              <p className="text-sm text-muted-foreground">
                {settings.mode === "mono"
                  ? "Base SQLite locale, sans authentification"
                  : "Base PostgreSQL, avec comptes utilisateurs"}
              </p>
            </div>
          </div>
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowModeSwitchDialog(!showModeSwitchDialog)}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Changer
            </Button>
          )}
        </div>
      </Card>

      {/* Mode switch dialog */}
      {showModeSwitchDialog && isAdmin && (
        <Card className="p-5 border-primary">
          {settings.mode === "mono" ? (
            <>
              <h3 className="font-semibold mb-4">Passer en multi-utilisateurs</h3>
              <form onSubmit={handleSwitchToMulti} className="space-y-4">
                <fieldset className="space-y-3">
                  <legend className="text-sm font-medium flex items-center gap-2 mb-2">
                    <Database className="h-4 w-4" /> PostgreSQL
                  </legend>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="col-span-2">
                      <Label htmlFor="sw_pg_host">H\u00f4te</Label>
                      <Input
                        id="sw_pg_host"
                        value={pgForm.pg_host}
                        onChange={(e) => setPgForm({ ...pgForm, pg_host: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="sw_pg_port">Port</Label>
                      <Input
                        id="sw_pg_port"
                        value={pgForm.pg_port}
                        onChange={(e) => setPgForm({ ...pgForm, pg_port: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="sw_pg_user">Utilisateur</Label>
                      <Input
                        id="sw_pg_user"
                        value={pgForm.pg_user}
                        onChange={(e) => setPgForm({ ...pgForm, pg_user: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="sw_pg_password">Mot de passe</Label>
                      <Input
                        id="sw_pg_password"
                        type="password"
                        value={pgForm.pg_password}
                        onChange={(e) => setPgForm({ ...pgForm, pg_password: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="sw_pg_database">Base</Label>
                    <Input
                      id="sw_pg_database"
                      value={pgForm.pg_database}
                      onChange={(e) => setPgForm({ ...pgForm, pg_database: e.target.value })}
                      required
                    />
                  </div>
                </fieldset>

                <fieldset className="space-y-3">
                  <legend className="text-sm font-medium flex items-center gap-2 mb-2">
                    <Shield className="h-4 w-4" /> Administrateur
                  </legend>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="sw_admin_user">Nom d'utilisateur</Label>
                      <Input
                        id="sw_admin_user"
                        value={pgForm.admin_username}
                        onChange={(e) =>
                          setPgForm({ ...pgForm, admin_username: e.target.value })
                        }
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="sw_admin_pass">Mot de passe</Label>
                      <Input
                        id="sw_admin_pass"
                        type="password"
                        value={pgForm.admin_password}
                        onChange={(e) =>
                          setPgForm({ ...pgForm, admin_password: e.target.value })
                        }
                        required
                      />
                    </div>
                  </div>
                </fieldset>

                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={pgForm.migrate_data}
                    onChange={(e) =>
                      setPgForm({ ...pgForm, migrate_data: e.target.checked })
                    }
                  />
                  Migrer les donn\u00e9es existantes vers le compte admin
                </label>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowModeSwitchDialog(false)}
                    disabled={loading}
                  >
                    Annuler
                  </Button>
                  <Button type="submit" disabled={loading}>
                    {loading ? "Migration..." : "Passer en multi"}
                  </Button>
                </div>
              </form>
            </>
          ) : (
            <>
              <h3 className="font-semibold mb-4">Passer en mono-utilisateur</h3>
              <form onSubmit={handleSwitchToMono} className="space-y-4">
                <div>
                  <Label htmlFor="sw_user_select">
                    Utilisateur dont conserver les documents
                  </Label>
                  <select
                    id="sw_user_select"
                    className="w-full border rounded-md p-2 text-sm"
                    value={selectedUserId}
                    onChange={(e) => setSelectedUserId(e.target.value)}
                    required
                  >
                    <option value="">S\u00e9lectionner un utilisateur</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.username}
                        {u.is_admin ? " (admin)" : ""}
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={includeAll}
                    onChange={(e) => setIncludeAll(e.target.checked)}
                  />
                  Inclure les documents de tous les utilisateurs
                </label>

                <p className="text-sm text-muted-foreground">
                  {includeAll
                    ? "Tous les documents seront migr\u00e9s vers la base SQLite locale."
                    : "Seuls les documents de l'utilisateur s\u00e9lectionn\u00e9 seront conserv\u00e9s."}
                </p>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowModeSwitchDialog(false)}
                    disabled={loading}
                  >
                    Annuler
                  </Button>
                  <Button type="submit" variant="destructive" disabled={loading}>
                    {loading ? "Migration..." : "Passer en mono"}
                  </Button>
                </div>
              </form>
            </>
          )}
        </Card>
      )}

      {/* User management (multi mode, admin only) */}
      {settings.mode === "multi" && isAdmin && currentUser && (
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Users className="h-4 w-4" /> Utilisateurs
            </h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggleRegistration}
              >
                Inscription : {settings.allow_registration ? "activ\u00e9e" : "d\u00e9sactiv\u00e9e"}
              </Button>
              <Button
                size="sm"
                onClick={() => setShowCreateUser(!showCreateUser)}
              >
                <UserPlus className="h-4 w-4 mr-1" />
                Ajouter
              </Button>
            </div>
          </div>

          {showCreateUser && (
            <form onSubmit={handleCreateUser} className="mb-4 flex gap-2">
              <Input
                placeholder="Nom d'utilisateur"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                minLength={3}
                required
                className="flex-1"
              />
              <Input
                placeholder="Mot de passe"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                required
                className="flex-1"
              />
              <Button type="submit" size="sm">
                Cr\u00e9er
              </Button>
            </form>
          )}

          <div className="space-y-2">
            {users.map((u) => (
              <div
                key={u.id}
                className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-accent/50"
              >
                <div>
                  <span className="font-medium">{u.username}</span>
                  {u.is_admin && (
                    <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                      admin
                    </span>
                  )}
                </div>
                {u.id !== currentUser.id && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteUser(u.id, u.username)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* App info */}
      <Card className="p-5">
        <p className="text-sm text-muted-foreground">
          {settings.app_name} v{settings.app_version}
        </p>
      </Card>
    </div>
  );
}
