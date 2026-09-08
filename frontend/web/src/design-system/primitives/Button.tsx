import type { ButtonHTMLAttributes } from "react";

/**
 * The one button treatment, as a shared class recipe rather than a
 * component that owns its element.
 *
 * WHY `buttonClass` AND NOT JUST `<Button>`. Half the "buttons" on the
 * public site are links -- a hero call to action is an `<a>`, an
 * app-store link is an external `<a>`, a real form control is a
 * `<button>`. A component that renders one of those forces every other
 * caller to fight it or wrap it. Exporting the class string lets a
 * `<Link>`, an `<a>` and a `<button>` all look identical without this
 * primitive needing to know `next/link` exists -- which keeps it usable
 * in the admin control centre and anywhere else, the whole point of the
 * layer.
 *
 * `<Button>` is here for the genuine `<button>` case (form submits in
 * the portal, later) so that case does not have to repeat the recipe.
 */

type Variant = "primary" | "secondary" | "accent" | "ghost";
type Size = "md" | "lg";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg font-semibold " +
  "transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "disabled:pointer-events-none disabled:opacity-60";

const SIZES: Record<Size, string> = {
  md: "px-5 py-2.5 text-sm",
  lg: "px-6 py-3.5 text-base",
};

/**
 * `onBrand` swaps each variant for the version that reads on a navy
 * panel -- the supplier hero and the closing call-to-action sit on
 * brand-blue, where the default outline and ghost styles disappear.
 */
const VARIANTS: Record<Variant, { light: string; onBrand: string }> = {
  primary: {
    light:
      "bg-brand-blue text-white hover:bg-brand-blue-light focus-visible:outline-brand-blue",
    onBrand:
      "bg-white text-brand-blue hover:bg-wash focus-visible:outline-white",
  },
  secondary: {
    light:
      "border border-line bg-white text-brand-blue hover:border-brand-blue hover:bg-wash focus-visible:outline-brand-blue",
    onBrand:
      "border border-white/30 text-white hover:bg-white/10 focus-visible:outline-white",
  },
  accent: {
    light:
      "bg-brand-green text-white hover:bg-brand-green-dark focus-visible:outline-brand-green",
    onBrand:
      "bg-brand-green text-white hover:bg-brand-green-dark focus-visible:outline-white",
  },
  ghost: {
    light:
      "text-brand-blue hover:bg-wash focus-visible:outline-brand-blue",
    onBrand: "text-white hover:bg-white/10 focus-visible:outline-white",
  },
};

export function buttonClass({
  variant = "primary",
  size = "lg",
  onBrand = false,
  className = "",
}: {
  variant?: Variant;
  size?: Size;
  onBrand?: boolean;
  className?: string;
} = {}): string {
  const v = VARIANTS[variant];
  return `${BASE} ${SIZES[size]} ${onBrand ? v.onBrand : v.light} ${className}`.trim();
}

export function Button({
  variant,
  size,
  onBrand,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  onBrand?: boolean;
}) {
  return (
    <button className={buttonClass({ variant, size, onBrand, className })} {...props} />
  );
}
