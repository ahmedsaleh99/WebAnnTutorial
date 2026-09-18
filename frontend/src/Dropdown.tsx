import { useEffect, useId, useRef, useState } from "react";

export interface DropdownOption<T extends string> {
  value: T;
  label: string;
}

export function Dropdown<T extends string>({ label, value, options, onChange }: {
  label: string;
  value: T;
  options: DropdownOption<T>[];
  onChange: (value: T) => void;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  const selected = options[selectedIndex];

  useEffect(() => {
    if (!open) return;
    optionRefs.current[activeIndex]?.focus();
    const closeOutside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, [open, activeIndex]);

  function show() {
    setActiveIndex(selectedIndex);
    setOpen(true);
  }

  function choose(option: DropdownOption<T>) {
    onChange(option.value);
    setOpen(false);
    triggerRef.current?.focus();
  }

  return <div className="dropdown-field" ref={rootRef} onBlur={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <span id={`${id}-label`}>{label}</span>
    <button ref={triggerRef} className="dropdown-trigger" type="button" role="combobox"
      aria-label={`${label}: ${selected?.label ?? ""}`} aria-expanded={open} aria-controls={`${id}-options`}
      aria-haspopup="listbox" onClick={() => open ? setOpen(false) : show()}
      onKeyDown={(event) => {
        if (!open && (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Home" || event.key === "End")) {
          event.preventDefault(); show();
        }
      }}>
      <span>{selected?.label}</span><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 7 5 5 5-5" /></svg>
    </button>
    {open && <div className="dropdown-menu" id={`${id}-options`} role="listbox" aria-label={label}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault(); event.stopPropagation();
          setOpen(false); triggerRef.current?.focus();
        } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault();
          setActiveIndex((index) => (index + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length);
        } else if (event.key === "Home" || event.key === "End") {
          event.preventDefault(); setActiveIndex(event.key === "Home" ? 0 : options.length - 1);
        }
      }}>
      {options.map((option, index) => <button key={option.value} ref={(element) => { optionRefs.current[index] = element; }}
        type="button" role="option" aria-selected={option.value === value}
        className={option.value === value ? "selected" : ""}
        onFocus={() => setActiveIndex(index)} onClick={() => choose(option)}>
        <span>{option.label}</span>{option.value === value && <span aria-hidden="true">✓</span>}
      </button>)}
    </div>}
  </div>;
}
