import { marketingImage, type MarketingImageKey } from "@/surfaces/marketing/imagery";
import type { CloudinaryOptions } from "@/lib/cloudinary";

/**
 * A responsive marketing photo, delivered from Cloudinary.
 *
 * A PLAIN `<img>`, DELIBERATELY. Cloudinary already does the two things
 * `next/image` would do for us -- per-device resizing (`w_` in the
 * srcset) and format negotiation (`f_auto`) -- and doing them at the CDN
 * means the bytes never round-trip through this app's server. On mobile
 * data that round trip is the cost that matters. This is the one place
 * in the codebase a raw `<img>` is the right call, so the lint rule is
 * silenced here and only here.
 *
 * WHEN THE PHOTO IS NOT AVAILABLE YET (no cloud name configured, asset
 * not uploaded) the component renders a brand panel in the exact same
 * box, so every page holds its shape before the imagery lands.
 */
export function CloudinaryImage({
  image,
  sizes,
  options,
  priority = false,
  className = "",
  rounded = "rounded-2xl",
}: {
  image: MarketingImageKey;
  /** The `sizes` attribute -- how wide the image renders at each breakpoint. */
  sizes: string;
  options?: CloudinaryOptions;
  /** Eager-load + high fetch priority. Use for an above-the-fold hero only. */
  priority?: boolean;
  className?: string;
  rounded?: string;
}) {
  const resolved = marketingImage(image, options);
  const aspectRatio = `${resolved.width} / ${resolved.height}`;

  if (!resolved.url) {
    return (
      <div
        aria-hidden
        style={{ aspectRatio }}
        className={`w-full overflow-hidden ${rounded} bg-brand-blue bg-[radial-gradient(120%_120%_at_15%_0%,#19376d_0%,#0b2447_45%,#051230_100%)] ${className}`}
      >
        <div className="h-full w-full bg-[radial-gradient(60%_60%_at_85%_100%,rgba(15,169,104,0.35)_0%,transparent_70%)]" />
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element -- see file header: Cloudinary handles resize + format at the CDN.
    <img
      src={resolved.url}
      srcSet={resolved.srcSet}
      sizes={sizes}
      alt={resolved.alt}
      width={resolved.width}
      height={resolved.height}
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
      style={{ aspectRatio }}
      className={`w-full ${rounded} object-cover ${className}`}
    />
  );
}
