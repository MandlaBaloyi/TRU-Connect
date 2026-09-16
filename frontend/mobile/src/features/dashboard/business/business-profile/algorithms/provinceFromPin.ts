import { PROVINCE_LABELS } from "../types";
import type { SouthAfricanProvince } from "../types";

/**
 * The province a map pin landed in, as one of our nine enum values.
 *
 * WHY THIS EXISTS. The map picker already hands back a province — it
 * comes with the pin, in the same response that gives us the town — and
 * we were throwing it away and then asking the person to pick it from a
 * list of nine. Mandla: "if they can use the map, we know they will
 * fill the province... we could just fill these based on what they
 * input on the location".
 *
 * NO EXTRA REQUEST, AND NO NEW MAPBOX USAGE. This reads a field already
 * present on the DeliveryLocation the picker returns, which is why it
 * does not touch the temporary-tier rule the geocoding provider works
 * under. Nothing is stored that was not already going to be stored;
 * this only stops us asking twice for one answer.
 *
 * IT MATCHES BY NORMALISED NAME, not by hoping the strings are equal.
 * The geocoder returns human spellings — "KwaZulu-Natal", "North-West",
 * "Northwest", sometimes "Gauteng Province" — and our enum is
 * SCREAMING_SNAKE. Both sides are reduced to letters only before
 * comparing, so hyphens, spaces and case stop mattering.
 *
 * UNRECOGNISED RETURNS undefined, NEVER A GUESS. A wrong province is
 * worse than a blank one: it is silently wrong on a field the person
 * believes they confirmed, and they have no reason to go back and look.
 * Blank leaves the picker in front of them.
 */

/** Letters only, lowercased: "KwaZulu-Natal" and "kwazulu natal" both
 *  become "kwazulunatal". */
function squash(value: string): string {
  return value.toLowerCase().replace(/[^a-z]/g, "");
}

const BY_SQUASHED_NAME: Record<string, SouthAfricanProvince> = Object.fromEntries(
  (Object.keys(PROVINCE_LABELS) as SouthAfricanProvince[]).flatMap((code) => [
    // The label, which is what a geocoder is most likely to return.
    [squash(PROVINCE_LABELS[code]), code],
    // And the code itself, in case a provider hands back the same
    // uppercase form we store.
    [squash(code), code],
  ])
);

/** Spellings a geocoder returns that are not our label and not our
 *  code. Kept deliberately short: each entry is a real string seen from
 *  a provider, not a guess at what one might say. */
const ALIASES: Record<string, SouthAfricanProvince> = {
  northwest: "NORTH_WEST",
  kwazulunatalprovince: "KWAZULU_NATAL",
  gautengprovince: "GAUTENG",
  limpopoprovince: "LIMPOPO",
  // "Transvaal" and the other pre-1994 names are deliberately ABSENT.
  // They map to areas that no longer correspond to one province, so any
  // mapping would be an invention.
};

export function provinceFromPin(raw: string | null | undefined): SouthAfricanProvince | undefined {
  if (!raw) return undefined;
  const key = squash(raw);
  return BY_SQUASHED_NAME[key] ?? ALIASES[key] ?? undefined;
}
