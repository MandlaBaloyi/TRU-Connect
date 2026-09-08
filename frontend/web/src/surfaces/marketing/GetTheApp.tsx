import { buttonClass } from "@/design-system/primitives/Button";
import { APP_STORE_URL, PLAY_STORE_URL } from "@/design-system/tokens/brand";

/**
 * The "get the app" call to action for businesses.
 *
 * THE STORE LINKS ARE NOT LIVE YET. `APP_STORE_URL` / `PLAY_STORE_URL`
 * are `"#"` placeholders in the brand tokens. A button that goes nowhere
 * is worse than an honest line of text, so until a real URL is set this
 * renders as a plain statement, not a link. The day the listings exist,
 * set the two constants and this becomes two working buttons with no
 * other change.
 */

const LIVE = PLAY_STORE_URL !== "#" || APP_STORE_URL !== "#";

export function GetTheApp({
  onBrand = false,
  size = "lg",
}: {
  onBrand?: boolean;
  size?: "md" | "lg";
}) {
  if (!LIVE) {
    return (
      <p
        className={`text-sm font-semibold ${
          onBrand ? "text-white/80" : "text-ink"
        }`}
      >
        Coming to Android and iPhone.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <a
        href={PLAY_STORE_URL}
        className={buttonClass({ variant: "primary", size, onBrand })}
      >
        Get it on Android
      </a>
      <a
        href={APP_STORE_URL}
        className={buttonClass({ variant: "secondary", size, onBrand })}
      >
        Get it on iPhone
      </a>
    </div>
  );
}
