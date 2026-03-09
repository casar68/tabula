import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAppSettings, getMe } from "@/lib/api";
import { getAccessToken, useAuthStore } from "@/lib/auth-store";

/**
 * Wraps protected routes. On mount:
 * 1. Checks /api/settings to see if setup is completed and what mode is active.
 * 2. If setup is not completed, redirects to /setup.
 * 3. If mode is "multi" and user is not authenticated, redirects to /login.
 * 4. Otherwise, renders children.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { setUser, setLoading, isLoading } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const settings = await getAppSettings();

        if (!settings.setup_completed) {
          navigate("/setup", { replace: true });
          return;
        }

        if (settings.mode === "multi") {
          const token = getAccessToken();
          if (!token) {
            navigate("/login", { replace: true });
            return;
          }

          try {
            const user = await getMe();
            if (!cancelled) {
              setUser(user);
              setReady(true);
            }
          } catch {
            if (!cancelled) {
              navigate("/login", { replace: true });
            }
          }
        } else {
          // Mono mode — no auth needed
          if (!cancelled) {
            setUser(null);
            setReady(true);
          }
        }
      } catch {
        // If settings endpoint fails, assume setup is needed
        if (!cancelled) {
          setLoading(false);
          setReady(true);
        }
      }
    }

    check();
    return () => {
      cancelled = true;
    };
  }, [navigate, setUser, setLoading]);

  if (!ready || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-muted-foreground">Chargement...</div>
      </div>
    );
  }

  return <>{children}</>;
}
