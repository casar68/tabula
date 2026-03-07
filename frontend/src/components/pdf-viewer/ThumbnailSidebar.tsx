import { Page } from "react-pdf";
import type { Selection, PageInfo } from "@/lib/types";

interface ThumbnailSidebarProps {
  pages: PageInfo[];
  selections: Selection[];
  activePage: number;
  onPageClick: (pageNumber: number) => void;
}

const THUMB_WIDTH = 120;

export function ThumbnailSidebar({
  pages,
  selections,
  activePage,
  onPageClick,
}: ThumbnailSidebarProps) {
  return (
    <div className="w-40 shrink-0 overflow-y-auto border-r bg-muted/30 p-2 space-y-2">
      {pages.map((page) => {
        const pageSelections = selections.filter(
          (s) => s.page === page.number
        );
        const isActive = activePage === page.number;
        const thumbScale = THUMB_WIDTH / page.width;

        return (
          <button
            key={page.number}
            className={`relative block w-full rounded border-2 transition-colors ${
              isActive ? "border-primary" : "border-transparent hover:border-primary/30"
            }`}
            onClick={() => onPageClick(page.number)}
          >
            <Page
              pageNumber={page.number}
              width={THUMB_WIDTH}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
            {/* Mini selection overlays */}
            {pageSelections.map((sel) => (
              <div
                key={sel.id}
                className="absolute border border-orange-500 bg-orange-500/20"
                style={{
                  left: sel.x1 * thumbScale,
                  top: sel.y1 * thumbScale,
                  width: (sel.x2 - sel.x1) * thumbScale,
                  height: (sel.y2 - sel.y1) * thumbScale,
                }}
              />
            ))}
            <span className="absolute bottom-0 right-0 text-[10px] bg-black/60 text-white px-1 rounded-tl">
              {page.number}
            </span>
          </button>
        );
      })}
    </div>
  );
}
