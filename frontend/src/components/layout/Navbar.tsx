import { Link, useLocation } from "react-router-dom";
import { FileText, LayoutTemplate, Info, HelpCircle } from "lucide-react";

const navItems = [
  { to: "/", label: "Mes fichiers", icon: FileText },
  { to: "/templates", label: "Mes templates", icon: LayoutTemplate },
  { to: "/about", label: "À propos", icon: Info },
  { to: "/help", label: "Aide", icon: HelpCircle },
];

export function Navbar() {
  const location = useLocation();

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg mr-8">
          <FileText className="h-6 w-6 text-primary" />
          Tabula
        </Link>
        <nav className="flex items-center gap-1">
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
      </div>
    </header>
  );
}
