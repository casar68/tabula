import { useSelectionStore } from "@/lib/store";
import type { Selection } from "@/lib/types";

const METHODS = [
  {
    value: "guess" as const,
    label: "Auto",
    description: "Détection automatique du type de tableau",
  },
  {
    value: "lattice" as const,
    label: "Lattice",
    description: "Pour les tableaux avec des bordures visibles",
  },
  {
    value: "stream" as const,
    label: "Stream",
    description: "Pour les tableaux sans bordures (espacement du texte)",
  },
];

interface MethodSelectorProps {
  onMethodChange: () => void;
}

export function MethodSelector({ onMethodChange }: MethodSelectorProps) {
  const selections = useSelectionStore((s) => s.selections);
  const updateSelection = useSelectionStore((s) => s.updateSelection);

  // Get the predominant method
  const currentMethod =
    selections.length > 0 ? selections[0].extraction_method : "guess";

  const handleChange = (method: Selection["extraction_method"]) => {
    for (const sel of selections) {
      updateSelection(sel.id, { extraction_method: method });
    }
    onMethodChange();
  };

  return (
    <div className="flex items-center gap-1">
      <span className="text-sm text-muted-foreground mr-2">Méthode :</span>
      {METHODS.map((m) => (
        <button
          key={m.value}
          className={`px-3 py-1 text-sm rounded-md transition-colors ${
            currentMethod === m.value
              ? "bg-primary text-primary-foreground"
              : "bg-muted hover:bg-muted/80 text-muted-foreground"
          }`}
          onClick={() => handleChange(m.value)}
          title={m.description}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
