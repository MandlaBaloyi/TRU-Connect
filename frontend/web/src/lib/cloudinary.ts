/**
 * Build a Cloudinary delivery URL.
 *
 * WHY THIS EXISTS. Marketing imagery is served straight from Cloudinary,
 * not from `public/` -- so a photo can be swapped without a deploy, and
 * so each device pulls a version sized and compressed for it. Someone is
 * opening this on mobile data. That means the URL is computed, not
 * written by hand, and this is where it is computed.
 *
 * PURE ON PURPOSE. `lib/` may not import anything else in `src/`, so the
 * cloud name is passed in rather than read from `@/config/env` here. The
 * marketing surface binds the two together (see
 * `surfaces/marketing/imagery.ts`).
 *
 * `f_auto,q_auto` is always applied: Cloudinary picks the format (WebP,
 * AVIF) and quality per request. Callers only decide dimensions and
 * crop.
 */

export type CloudinaryOptions = {
  width?: number;
  height?: number;
  /** Cloudinary crop mode, e.g. "fill", "fit", "scale". Default "fill". */
  crop?: "fill" | "fit" | "scale" | "thumb";
  /** Focus point for a crop, e.g. "auto", "face", "center". */
  gravity?: string;
  /** 1-100, or "auto" (the default). */
  quality?: number | "auto";
  dpr?: number | "auto";
};

/**
 * Returns the delivery URL, or `null` when it cannot be built -- no
 * cloud name configured, or no public id. Callers render a fallback
 * rather than a broken image.
 */
export function cloudinaryUrl(
  cloudName: string | undefined,
  publicId: string | undefined,
  options: CloudinaryOptions = {},
): string | null {
  if (!cloudName || !publicId) return null;

  const { width, height, crop = "fill", gravity, quality = "auto", dpr } = options;

  const transforms = [
    "f_auto",
    `q_${quality}`,
    width && `w_${Math.round(width)}`,
    height && `h_${Math.round(height)}`,
    (width || height) && `c_${crop}`,
    gravity && `g_${gravity}`,
    dpr && `dpr_${dpr}`,
  ].filter(Boolean);

  const id = publicId.replace(/^\/+/, "");
  return `https://res.cloudinary.com/${cloudName}/image/upload/${transforms.join(",")}/${id}`;
}

/**
 * A `srcSet` string for a set of target widths, for a plain responsive
 * `<img>`. Returns `""` when the URL cannot be built.
 */
export function cloudinarySrcSet(
  cloudName: string | undefined,
  publicId: string | undefined,
  widths: number[],
  options: CloudinaryOptions = {},
): string {
  return widths
    .map((w) => {
      const url = cloudinaryUrl(cloudName, publicId, { ...options, width: w });
      return url ? `${url} ${w}w` : null;
    })
    .filter(Boolean)
    .join(", ");
}
