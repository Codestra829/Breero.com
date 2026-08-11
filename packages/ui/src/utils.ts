import type { ReactNode } from "react";

export function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export type IconProps = { className?: string; size?: number; "aria-hidden"?: boolean };

export type WithChildren = { children?: ReactNode };
