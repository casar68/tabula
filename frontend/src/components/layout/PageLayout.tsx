import type { ReactNode } from "react";

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  actions?: ReactNode;
  fullWidth?: boolean;
}

export function PageLayout({
  children,
  title,
  actions,
  fullWidth = false,
}: PageLayoutProps) {
  return (
    <main className={fullWidth ? "w-full" : "container mx-auto px-4 py-6"}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-6">
          {title && <h1 className="text-2xl font-bold">{title}</h1>}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </main>
  );
}
