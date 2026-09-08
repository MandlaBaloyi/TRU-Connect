import { CLOUDINARY_CLOUD_NAME } from "@/config/env";
import {
  cloudinarySrcSet,
  cloudinaryUrl,
  type CloudinaryOptions,
} from "@/lib/cloudinary";

/**
 * The marketing site's image catalogue: every photo the public pages
 * use, named once here with its Cloudinary public id, its intrinsic
 * aspect ratio, and its alt text.
 *
 * THE PUBLIC IDS BELOW ARE PLACEHOLDERS. They follow the folder
 * convention `truconnect/marketing/<name>` so the real uploads can drop
 * straight in. Until `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` is set and the
 * assets exist, `marketingImage()` returns `{ url: null }` and
 * `<CloudinaryImage>` renders a brand-tinted panel in the same box --
 * the layout is right whether or not the photo has landed.
 *
 * Alt text lives here, not at the call site, because it is a property of
 * the image, not of the page -- and writing it once stops it drifting.
 */

export type MarketingImageKey =
  | "homeHero"
  | "suppliersHero"
  | "aboutStory";

type MarketingImageSpec = {
  publicId: string;
  /** Intrinsic width/height, used only for the aspect-ratio box. */
  width: number;
  height: number;
  alt: string;
};

const IMAGES: Record<MarketingImageKey, MarketingImageSpec> = {
  homeHero: {
    publicId: "truconnect/marketing/home-hero",
    width: 1280,
    height: 960,
    alt: "A shopkeeper checking stock on their phone behind the counter of a small store.",
  },
  suppliersHero: {
    publicId: "truconnect/marketing/suppliers-hero",
    width: 1280,
    height: 960,
    alt: "A wholesaler loading boxes of stock for delivery to independent retailers.",
  },
  aboutStory: {
    publicId: "truconnect/marketing/about-story",
    width: 1280,
    height: 854,
    alt: "A busy street of independent shops and traders in South Africa.",
  },
};

/** The widths we ask Cloudinary for, covering 1x and 2x common layouts. */
const SRCSET_WIDTHS = [480, 640, 828, 1080, 1280, 1600];

export type ResolvedMarketingImage = {
  /** The 1x/default src, or null when the URL cannot be built yet. */
  url: string | null;
  srcSet: string;
  width: number;
  height: number;
  alt: string;
};

export function marketingImage(
  key: MarketingImageKey,
  options: CloudinaryOptions = {},
): ResolvedMarketingImage {
  const spec = IMAGES[key];
  return {
    url: cloudinaryUrl(CLOUDINARY_CLOUD_NAME, spec.publicId, {
      width: spec.width,
      ...options,
    }),
    srcSet: cloudinarySrcSet(
      CLOUDINARY_CLOUD_NAME,
      spec.publicId,
      SRCSET_WIDTHS,
      options,
    ),
    width: spec.width,
    height: spec.height,
    alt: spec.alt,
  };
}
