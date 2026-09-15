import React, { useState } from "react";
import { useRouter } from "expo-router";

import { ChipSingleSelect } from "@/features/dashboard/business/business-profile/components";
import { useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks";
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

  const [restockRhythm, setRestockRhythm] = useState<RestockRhythm | undefined>();
  const [weeklySpendBand, setWeeklySpendBand] = useState<WeeklySpendBand | undefined>();
  const [error, setError] = useState<string | null>(null);

  const handleContinue = async () => {
    setError(null);
    try {
      await saveTradingDetails({ restockRhythm, weeklySpendBand });
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
      promise="This is how we know when to show you something, and what size order makes sense."
      onPrimary={handleContinue}
      primaryDisabled={!restockRhythm || !weeklySpendBand}
      isSaving={isSavingTradingDetails}
      error={error}
    >
      <ChipSingleSelect
        label="How often do you restock?"
        options={RESTOCK_OPTIONS}
        value={restockRhythm}
        onChange={(v) => setRestockRhythm((v as RestockRhythm) || undefined)}
      />
      <ChipSingleSelect
        label="Roughly what do you spend on stock a week?"
        options={SPEND_OPTIONS}
        value={weeklySpendBand}
        onChange={(v) => setWeeklySpendBand((v as WeeklySpendBand) || undefined)}
      />
    </SetupStepScaffold>
  );
}
