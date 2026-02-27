import { useState, useRef, useEffect } from "react";

interface Props {
  value: string;
  placeholder?: string;
  onSave: (value: string) => void;
  suggestions?: string[];
}

export default function EditableField({
  value,
  placeholder = "Click to set",
  onSave,
  suggestions = [],
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
    }
  }, [editing]);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  const commit = () => {
    setEditing(false);
    const trimmed = draft.trim();
    if (trimmed !== value) {
      onSave(trimmed);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") commit();
    if (e.key === "Escape") {
      setDraft(value);
      setEditing(false);
    }
  };

  if (editing) {
    return (
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          list="editable-field-suggestions"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={handleKeyDown}
          className="w-full rounded border border-blue-500 bg-gray-800 px-2 py-0.5 text-sm text-white outline-none"
          placeholder={placeholder}
        />
        {suggestions.length > 0 && (
          <datalist id="editable-field-suggestions">
            {suggestions.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => setEditing(true)}
      className="group flex items-center gap-1 text-right"
      title="Click to edit"
    >
      <span>{value || <span className="italic text-gray-600">{placeholder}</span>}</span>
      <svg
        className="h-3 w-3 text-gray-600 opacity-0 transition-opacity group-hover:opacity-100"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
        />
      </svg>
    </button>
  );
}
