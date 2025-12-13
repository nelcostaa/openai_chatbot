import { cn } from "@/lib/utils";

interface AgeSelectionCardsProps {
  onSelect: (ageRange: string, marker: string) => void;
  selectedAge?: string;
  disabled?: boolean;
}

// Age ranges with their display labels and backend keys
const ageRanges = [
  { id: "under_18", label: "Under 18", number: "1" },
  { id: "18_30", label: "18 – 30", number: "2" },
  { id: "31_45", label: "31 – 45", number: "3" },
  { id: "46_60", label: "46 – 60", number: "4" },
  { id: "61_plus", label: "61 and over", number: "5" },
];

export function AgeSelectionCards({ onSelect, selectedAge, disabled }: AgeSelectionCardsProps) {
  const handleSelect = (age: typeof ageRanges[0]) => {
    if (disabled) return;
    // Send the age range ID and a marker that backend can detect
    const marker = `[Age selected via button: ${age.id}]`;
    onSelect(age.id, marker);
  };

  return (
    <div className="self-start max-w-full message-appear">
      <div className="flex flex-wrap gap-3 p-5 bg-bubble-ai rounded-2xl rounded-tl-md">
        <p className="w-full text-lg text-foreground mb-2">Please select your age range:</p>
        {ageRanges.map((age) => (
          <button
            key={age.id}
            onClick={() => handleSelect(age)}
            disabled={disabled}
            className={cn(
              "px-6 py-4 rounded-xl border-2 text-lg font-medium transition-all",
              "hover:border-primary hover:bg-primary/5",
              "focus:outline-none focus:ring-2 focus:ring-primary/30",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              selectedAge === age.id
                ? "border-primary bg-primary/10 text-foreground"
                : "border-border bg-card text-foreground"
            )}
          >
            {age.label}
          </button>
        ))}
      </div>
    </div>
  );
}
