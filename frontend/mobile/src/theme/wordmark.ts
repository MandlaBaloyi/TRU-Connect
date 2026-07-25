/**
 * TRU Connect wordmark styling tokens.
 *
 * Used only by BrandTopBar -- the persistent, logo-free brand mark shown
 * across the 5 primary dashboard tabs (Home / Account / Community /
 * Discovery / More). Kept separate from typography.ts so this one-off
 * treatment doesn't leak into the general type scale.
 *
 * Treatment: "Tru" in solid navy, "Connect" in italic emerald green --
 * a typographic echo of the two-tone infinity logo, without using the
 * logo mark itself.
 */
import { palette } from "./colors";

export const wordmark = {
  fontSize: 20,
  letterSpacing: -0.3,
  truPart: {
    fontWeight: "700" as const,
    fontStyle: "normal" as const,
    color: palette.truePointBlue,
  },
  connectPart: {
    fontWeight: "700" as const,
    fontStyle: "italic" as const,
    color: palette.emeraldGreen,
  },
};

/** Dark-mode variant, if/when BrandTopBar is made theme-aware. */
export function getWordmarkColors(isDark: boolean) {
  return {
    tru: isDark ? palette.truePointBlueLight : palette.truePointBlue,
    connect: isDark ? palette.emeraldGreenLight : palette.emeraldGreen,
  };
}