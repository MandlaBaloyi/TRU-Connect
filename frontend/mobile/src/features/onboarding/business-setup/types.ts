/**
 * The three questions a shop answers before it reaches its dashboard.
 *
 * WHY THESE THREE AND NOT SEVEN. Every field here is read by the
 * demand engine — they are the whole of what backend
 * demand/signals/declared.py takes off the profile. My Business holds
 * eleven further columns that nothing outside its own screen reads,
 * and not one of them is asked here (V2_18 Part 1). A nullable column
 * nobody queries costs nothing; a question at signup costs a person
 * who closes the app.
 *
 * THE SERVER DECIDES WHAT IS MISSING, not this file. The step ids
 * below mirror backend setup_service.ALL_STEPS, and `nextStep` comes
 * off the wire — so the app never holds its own opinion about the
 * order and the two cannot disagree about which step somebody is on.
 */

export type SetupStepId = "whatYouBuy" | "howYouBuy" | "whereYouAre";

export interface SetupState {
  steps: Record<SetupStepId, boolean>;
  /** The gate. True once steps one and two are answered, whatever
   *  happened to the third — which is skippable, so it never blocks. */
  requiredComplete: boolean;
  /** All three, including the skippable one. Distinct from
   *  requiredComplete precisely so a skipped location stays visible as
   *  unfinished without ever locking anybody out. */
  isComplete: boolean;
  nextStep: SetupStepId | null;
}

/** Where each step lives, so the gate and the "next" buttons read the
 *  same map rather than each spelling the routes out. */
export const SETUP_ROUTES: Record<SetupStepId, string> = {
  whatYouBuy: "/(setup)/step-1-your-shop",
  howYouBuy: "/(setup)/step-2-how-you-buy",
  whereYouAre: "/(setup)/step-3-where-you-are",
};

export const SETUP_STEP_ORDER: SetupStepId[] = ["whatYouBuy", "howYouBuy", "whereYouAre"];
