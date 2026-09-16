import React, { useEffect, useState } from "react";
import { useRouter } from "expo-router";

import { SelectField } from "@/components/forms/SelectField";
import { useBusinessProfile, useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks";
import { CUSTOMER_TYPE_LABELS } from "@/features/dashboard/business/business-profile/types";
import type { CustomerType } from "@/features/dashboard/business/business-profile/types";
import { CATEGORY_OPTIONS } from "@/constants/productCategories";

import { SetupStepScaffold } from "../components/SetupStepScaffold";
import { useRefreshBusinessSetup } from "../hooks/useBusinessSetup";
import { SETUP_ROUTES } from "../types";

const BUYS_OPTIONS = CATEGORY_OPTIONS.map((o) => ({ value: o.value as string, label: o.label }));
const CUSTOMER_TYPE_OPTIONS = (
  Object.keys(CUSTOMER_TYPE_LABELS) as (keyof typeof CUSTOMER_TYPE_LABELS)[]
).map((value) => ({ value, label: CUSTOMER_TYPE_LABELS[value] }));

/**
 * Step one — what this shop buys.
 *
 * THE SINGLE MOST VALUABLE ANSWER IN THE APP. buys_categories is what
 * "stock for your shop" is built from, what gates the sponsored slot,
 * and what the category chips lean on. A shop that answers only this
 * and nothing else already has a Community tab worth opening; a shop
 * that answers everything else and not this does not.
 *
 * IT ASKS WHAT THEY BUY, NOT WHAT THEY SELL, and that reversal is the
 * whole reason the field is worth collecting. The form used to ask
 * what a business SELLS from a per-category list of adjectives, and
 * for five of the eight categories — including RETAIL, which is what a
 * spaza picks — the available answer was the word "Products". There
 * was nothing to read. A salon SELLS haircuts and BUYS relaxers; only
 * the second is orderable here.
 *
 * WHY IT DOES NOT ASK FOR THE BUSINESS NAME. Registration requires it
 * now (auth_schemas.BusinessRegisterSchema), so asking again would be
 * asking a question whose answer is already on the row — and the name
 * is identity rather than fuel: the demand engine never reads it.
 *
 * CUSTOMER TYPES IS ON THIS SCREEN AND DOES NOT GATE IT. It feeds
 * prefers_bulk, a refinement of the model categories create. Blocking
 * somebody on the less important half of a question is how a setup
 * flow starts feeling like an interview.
 */
export default function StepYourShop() {
  const router = useRouter();
  const refreshSetup = useRefreshBusinessSetup();
  const { saveTradingDetails, isSavingTradingDetails } = useBusinessProfileMutations();
  const { profile } = useBusinessProfile();

  const [buysCategories, setBuysCategories] = useState<string[]>([]);
  const [customerTypes, setCustomerTypes] = useState<CustomerType[]>([]);
  const [prefilled, setPrefilled] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // PREFILL ONCE, FROM WHAT IS SAVED. Without this, arriving here from
  // step two's back arrow -- or simply reopening the app mid-flow --
  // shows an empty form, which reads as "it lost my answer" and
  // invites somebody to fill it in a second time.
  //
  // GUARDED BY `prefilled` RATHER THAN BY EMPTINESS. Keying off
  // "is the draft still empty" would re-apply the saved value every
  // time the query refetched, so clearing a selection would silently
  // undo itself.
  useEffect(() => {
    if (profile && !prefilled) {
      setBuysCategories(profile.tradingDetails.buysCategories ?? []);
      setCustomerTypes(profile.tradingDetails.customerTypes ?? []);
      setPrefilled(true);
    }
  }, [profile, prefilled]);

  const handleContinue = async () => {
    setError(null);
    try {
      // WRITES THROUGH THE PROFILE'S OWN MUTATION, not a setup-specific
      // one. Same service, same validation, same audit path as editing
      // the identical field in My Business later.
      await saveTradingDetails({ buysCategories, customerTypes });
      await refreshSetup();
      router.replace(SETUP_ROUTES.howYouBuy as never);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <SetupStepScaffold
      step="whatYouBuy"
      title="What stock do you buy?"
      why={[
        "This is the answer that fills your Community tab. We use it to show you stock in the categories you actually restock, and suppliers who carry it.",
        "Pick everything you buy, even occasionally — a category you leave out is one we will never show you.",
        "It is only ever used to choose what appears in your feed. It is not shown to suppliers and it is not a credit check.",
      ]}
      onPrimary={handleContinue}
      primaryDisabled={buysCategories.length === 0}
      isSaving={isSavingTradingDetails}
      error={error}
    >
      {/* A FIELD AND A SHEET, NOT SEVENTEEN CHIPS. The chip wall filled
          the screen before anything had been answered and pushed the
          second question below the fold. See SelectField. */}
      <SelectField
        label="Stock you buy"
        sheetTitle="What stock do you buy?"
        options={BUYS_OPTIONS}
        value={buysCategories}
        onChange={setBuysCategories}
        multiple
        placeholder="Tap to choose your categories"
      />
      {/* A SHEET TOO, THOUGH FIVE OPTIONS WOULD FIT AS CHIPS.
          Consistency wins here: this is the SAME QUESTION as the one
          on My Business > Trading details, and having it look like a
          chip row in one place and a field in the other is worse than
          either choice on its own. A form whose questions all have one
          shape also reads as one form rather than a collection of
          widgets. */}
      <SelectField
        label="Who do you mainly sell to? (optional)"
        options={CUSTOMER_TYPE_OPTIONS}
        value={customerTypes}
        onChange={(v) => setCustomerTypes(v as CustomerType[])}
        multiple
        placeholder="Tap to choose"
      />
    </SetupStepScaffold>
  );
}
