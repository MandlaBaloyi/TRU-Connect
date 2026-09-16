/**
 * Business Profile — completion calculation. PURE.
 *
 * Deliberately narrow: only REQUIRED and RECOMMENDED fields count
 * toward the percentage. OPTIONAL fields (physical address, social
 * links, operating hours, employee count) never block or dilute the
 * number — matches the spec's explicit "the goal is completion, not
 * gamification" and "under 5 minutes" requirements.
 *
 * THIS IS NOW THE ONLY ANSWER TO "HOW COMPLETE IS THIS PROFILE". There
 * used to be a second one -- business_info_complete and
 * location_complete on the row, feeding a separate Verification
 * checklist -- and it was worse in both directions: nothing ever wrote
 * those columns, and a column has to be remembered while this is
 * derived from the data every time it is read. Both are gone (V2_18
 * Part 2). Nothing on this screen passes judgement on a business any
 * more; it measures how much they have told us, which is a question
 * the demand engine genuinely acts on.
 */
import type { BusinessProfile, ProfileCompletion, ProfileSectionKey } from "../types";

interface FieldCheck {
  section: ProfileSectionKey;
  isFilled: (profile: BusinessProfile) => boolean;
}

/** The tracked fields. Order doesn't matter for the calculation, only
 *  for readability here. Recommended fields (category, business type,
 *  location, trading basics) are included alongside required ones —
 *  there's no separate weighting, since splitting hairs between
 *  "required" and "recommended" in the number itself would just be
 *  gamification the spec explicitly warns against. */
const TRACKED_FIELDS: FieldCheck[] = [
  { section: "businessDetails", isFilled: (p) => p.businessDetails.businessName.trim().length > 0 },
  { section: "businessDetails", isFilled: (p) => Boolean(p.businessDetails.category) },
  { section: "businessDetails", isFilled: (p) => Boolean(p.businessDetails.businessType) },

  { section: "contactDetails", isFilled: (p) => Boolean(p.contactDetails.phone) },

  { section: "location", isFilled: (p) => Boolean(p.location.province) },
  { section: "location", isFilled: (p) => Boolean(p.location.cityOrTown) },
  { section: "location", isFilled: (p) => Boolean(p.businessDetails.operatingModel) },

  // WHAT COUNTS AS COMPLETE CHANGED WITH THE FIELDS. orderChannels and
  // paymentMethods described how orders and money reach THEIR
  // customers — real for them, invisible to the feed — so they no
  // longer cost a shopkeeper a question or dent their percentage.
  // What is counted now is exactly what the demand engine reads.
  { section: "tradingDetails", isFilled: (p) => p.tradingDetails.buysCategories.length > 0 },
  { section: "tradingDetails", isFilled: (p) => Boolean(p.tradingDetails.restockRhythm) },
  { section: "tradingDetails", isFilled: (p) => Boolean(p.tradingDetails.weeklySpendBand) },

  { section: "operatingHistory", isFilled: (p) => Boolean(p.operatingHistory.yearsOperating) },

  // Supplier info is fully optional per the spec — deliberately NOT
  // tracked here, so an empty selection never dents the percentage.
];

export function calculateProfileCompletion(profile: BusinessProfile): ProfileCompletion {
  const sectionTotals: Record<ProfileSectionKey, { met: number; total: number }> = {
    businessDetails: { met: 0, total: 0 },
    contactDetails: { met: 0, total: 0 },
    location: { met: 0, total: 0 },
    tradingDetails: { met: 0, total: 0 },
    operatingHistory: { met: 0, total: 0 },
    supplierInfo: { met: 0, total: 0 },
  };

  let totalMet = 0;
  TRACKED_FIELDS.forEach((field) => {
    sectionTotals[field.section].total += 1;
    if (field.isFilled(profile)) {
      sectionTotals[field.section].met += 1;
      totalMet += 1;
    }
  });

  const overallPercent = Math.round((totalMet / TRACKED_FIELDS.length) * 100);

  const sections = Object.fromEntries(
    (Object.keys(sectionTotals) as ProfileSectionKey[]).map((key) => [
      key,
      {
        isComplete: sectionTotals[key].total === 0 || sectionTotals[key].met === sectionTotals[key].total,
        requiredFieldsMet: sectionTotals[key].met,
        requiredFieldsTotal: sectionTotals[key].total,
      },
    ])
  ) as ProfileCompletion["sections"];

  return { overallPercent, sections };
}
