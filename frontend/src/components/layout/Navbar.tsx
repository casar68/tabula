import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FileText,
  LayoutTemplate,
  Info,
  HelpCircle,
  Settings,
  LogOut,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";

const navItems = [
  { to: "/", label: "Mes fichiers", icon: FileText },
  { to: "/templates", label: "Mes templates", icon: LayoutTemplate },
  { to: "/settings", label: "Param\u00e8tres", icon: Settings },
  { to: "/about", label: "\u00c0 propos", icon: Info },
  { to: "/help", label: "Aide", icon: HelpCircle },
];

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg mr-8">
          <FileText className="h-6 w-6 text-primary" />
          Tabula
        </Link>
        <nav className="flex items-center gap-1 flex-1">
          {navItems.map((item) => {
            const isActive =
              item.to === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-accent text-accent-foreground font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User menu (multi mode only) */}
        {isAuthenticated && user && (
          <div className="flex items-center gap-2 ml-4">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <User className="h-3.5 w-3.5" />
              {user.username}
              {user.is_admin && (
                <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded ml-1">
                  admin
                </span>
              )}
            </span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
