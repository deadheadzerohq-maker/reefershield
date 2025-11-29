import * as React from "react";
import { cn } from "@/lib/utils";

interface SwitchProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export function Switch({ checked, onCheckedChange, className, ...props }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange && onCheckedChange(!checked)}
      className={cn(
        "inline-flex h-6 w-10 items-center rounded-full border border-slate-700 bg-slate-900 px-0.5 transition-colors",
        checked && "bg-cyan-400 border-cyan-300",
        className
      )}
      {...props}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform",
          checked && "translate-x-4"
        )}
      />
    </button>
  );
}
