import React, { useEffect, useState } from "react";
import { useRouter } from "expo-router";

import { SelectField } from "@/components/forms/SelectField";
import { useBusinessProfile, useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks";
import {
  RESTOCK_RHYTHM_LABELS,
  WEEKLY_SPEND_BAND_LABELS,
} from "@/features/dashboard/business/business-profile/types";
import type {
  RestockRhythm,
  WeeklySpendBand,
} from "@/features/dashboard/business/business-profile/types";

import { SetupStepScaffold } from "../components/SetupStepScaffold";
import { useRefreshBusinessSetup } from "../hooks/useBusinessSetup";
import { SETUP_ROUTES } from "../types";

const RESTOCK_OPTIONS = (Object.keys(RESTOCK_RHYTHM_LABELS) as RestockRhythm[]).map((value) => ({
  value,
  label: RESTOCK_RHYTHM_LABELS[value],
}));
const SPEND_OPTIONS = (Object.keys(WEEKLY_SPEND_BAND_LABELS) as WeeklySpendBand[]).map((value) => ({
  value,
  label: WEEKLY_SPEND_BAND_LABELS[value],
}));

// PHRASED AS THE SHOP'S OWN SITUATION, not as a yes/no to a question
// about transport. "I can fetch it myself" is something a shopkeeper
// recognises instantly; "Do you have collection capability" is a form.
const COLLECT_OPTIONS = [
  { value: "YES", label: "Yes, I can fetch stock myself" },
  { value: "NO", label: "No, it must be delivered to me" },
];

/**
 * Step two — how often, and how much.
 *
 * TOGETHER THEY LET THE FEED BE USEFUL BEFORE A SINGLE ORDER EXISTS.
 * Rhythm becomes cadence_days, which is how the engine knows when a
 * shop is due; spend becomes order_ceiling_cents, which is how it
 * stops showing a R5,000 pallet to somebody who buys R800 a week.
 * Without them the engine waits months for order history, and a shop
 * that restocks daily is served exactly as badly as one that restocks
 * monthly in the meantime.
 *
 * BOTH ARE REQUIRED HERE AND NEITHER SUBSTITUTES. They answer
 * different questions — WHEN to press and WHAT SIZE to show — so a
 * shop with one of them gets half a model. That is the rule
 * setup_service.STEP_HOW_YOU_BUY encodes, and this screen simply
 * reflects it.
 *
 * SPEND IS A BAND, NEVER A NUMBER, and it is not a financial
 * assessment. An exact figure is a question people hesitate over, get
 * wrong, and feel examined by — and the engine does not need
 * precision, it needs to size a basket. V2_03 is explicit that
 * self-reported figures cannot support lending, and this is
 * self-reported.
 *
 * "WHEN I RUN OUT" IS A REAL ANSWER. IRREGULAR is offered because
 * plenty of shops buy when they are empty and when they have cash, and
 * recording that honestly beats forcing a cadence the engine will then
 * be wrong about.
 */
export default function StepHowYouBuy() {
  const router = useRouter();
  const refreshSetup = useRefreshBusinessSetup();
  const { saveTradingDetails, isSavingTradingDetails } = useBusinessProfileMutations();
  const { profile } = useBusinessProfile();

  const [restockRhythm, setRestockRhythm] = useState<RestockRhythm | undefined>();
  const [weeklySpendBand, setWeeklySpendBand] = useState<WeeklySpendBand | undefined>();
  // undefined === "not answered", and it stays undefined all the way to
  // the column. It is NOT initialised to false.
  const [canCollect, setCanCollect] = useState<boolean | undefined>();
  const [prefilled, setPrefilled] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // See StepYourShop for why this is guarded by a flag rather than by
  // the draft being empty.
  useEffect(() => {
    if (profile && !prefilled) {
      setRestockRhythm(profile.tradingDetails.restockRhythm);
      setWeeklySpendBand(profile.tradingDetails.weeklySpendBand);
      // ?? undefined, NOT `|| undefined` -- false is a real answer here
      // and must survive a reopen.
      setCanCollect(profile.tradingDetails.canCollect ?? undefined);
      setPrefilled(true);
    }
  }, [profile, prefilled]);

  const handleContinue = async () => {
    setError(null);
    try {
      await saveTradingDetails({ restockRhythm, weeklySpendBand, canCollect });
      await refreshSetup();
      router.replace(SETUP_ROUTES.whereYouAre as never);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <SetupStepScaffold
      step="howYouBuy"
      title="How do you buy stock?"
      why={[
        "How often you restock tells us WHEN to put something in front of you — a shop that buys daily and one that buys monthly should not see the same feed on the same morning.",
        "The weekly amount tells us WHAT SIZE to show. It stops us putting a R5,000 pallet in front of a shop that buys R800 at a time.",
        "It is a rough band, never an exact figure, and it is not a credit check or a financial assessment. Nobody but you sees it.",
        "Whether you can collect is optional. Answer it and a supplier who only does collection stops being suggested to you if you have no transport — leave it and nothing changes either way.",
      ]}
      onPrimary={handleContinue}
      primaryDisabled={!restockRhythm || !weeklySpendBand}
      isSaving={isSavingTradingDetails}
      error={error}
    >
      {/* FIELDS, NOT CHIPS, to match step one -- six rhythms and five
          bands is not a wall on its own, but two chip blocks stacked
          push the Continue button off a small screen, and a signup
          flow whose questions change shape between steps reads as
          three screens rather than one flow. */}
      <SelectField
        label="How often do you restock?"
        options={RESTOCK_OPTIONS}
        value={restockRhythm ? [restockRhythm] : []}
        onChange={(v) => setRestockRhythm(v[0] as RestockRhythm | undefined)}
        placeholder="Tap to choose"
      />
      <SelectField
        label="Roughly what do you spend on stock a week?"
        sheetTitle="Weekly spend on stock"
        options={SPEND_OPTIONS}
        value={weeklySpendBand ? [weeklySpendBand] : []}
        onChange={(v) => setWeeklySpendBand(v[0] as WeeklySpendBand | undefined)}
        placeholder="Tap to choose"
      />
      {/* OPTIONAL, AND UNANSWERED IS NOT "NO". The field is tri-state
          all the way down to the column; leaving it blank means we
          never asked, and the feed behaves exactly as it did before
          the question existed. Only an explicit "I need delivery"
          changes anything. */}
      <SelectField
        label="Can you collect your own stock? (optional)"
        sheetTitle="Collecting stock"
        options={COLLECT_OPTIONS}
        value={canCollect === undefined || canCollect === null ? [] : [canCollect ? "YES" : "NO"]}
        onChange={(v) => setCanCollect(v.length === 0 ? undefined : v[0] === "YES")}
        placeholder="Tap to choose"
      />
    </SetupStepScaffold>
  );
}
