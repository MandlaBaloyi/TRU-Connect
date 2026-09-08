import Link from "next/link";

import { PageHeading } from "@/design-system/primitives/PageHeading";
import { Section } from "@/design-system/patterns/Section";
import { routes } from "@/config/routes";
import { SUPPLIER_PLANS } from "@/surfaces/marketing/siteContent";

/**
 * Plans for suppliers.
 *
 * THE CAPS ARE REAL AND THE PRICES ARE NOT INVENTED. Every monthly limit
 * shown here is enforced in the backend's own tier definitions. No price
 * has been set for any tier anywhere in the system, so this page says
 * "talk to us" rather than printing a number nobody has decided.
 *
 * That is not a placeholder to be quietly filled in later with whatever
 * looks plausible. A price a supplier reads here and does not get is the
 * kind of lie discovered after they have committed -- which is the one
 * moment it costs the most.
 *
 * THE CAP IS EXPLAINED, NOT JUST LISTED. "R10,000 a month" means nothing
 * without knowing what it counts, and a supplier who thinks it caps
 * their turnover will assume the platform is useless to them. It counts
 * only money that moves OUTSIDE TruConnect, which is a compliance
 * boundary rather than a commercial one.
 */
export function Pricing() {
  return (
    <>
      <Section>
        <PageHeading
          eyebrow="Pricing"
          title="Start free. Talk to us when you outgrow it."
          lead="Every plan lets you list your products and take orders. The difference is how your catalogue gets in, and how much you can take in direct payments each month."
        />
      </Section>

      <Section>
        <div className="grid gap-6 lg:grid-cols-3">
          {SUPPLIER_PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-2xl border p-7 ${
                plan.highlight
                  ? "border-brand-blue bg-brand-blue text-white shadow-lg"
                  : "border-line/70 bg-white"
              }`}
            >
              <h2
                className={`text-2xl font-bold tracking-tight ${
                  plan.highlight ? "text-white" : "text-brand-blue"
                }`}
              >
                {plan.name}
              </h2>
              <p className={`mt-2 text-sm ${plan.highlight ? "text-white/75" : "text-ink-muted"}`}>
                {plan.forWho}
              </p>

              <div className="mt-6">
                <p className={`text-3xl font-bold ${plan.highlight ? "text-white" : "text-ink"}`}>
                  {plan.price}
                </p>
                <p
                  className={`mt-1 text-xs ${plan.highlight ? "text-white/60" : "text-ink-muted"}`}
                >
                  {plan.priceNote}
                </p>
              </div>

              <div
                className={`mt-6 rounded-lg px-4 py-3 ${
                  plan.highlight ? "bg-white/10" : "bg-wash"
                }`}
              >
                <p
                  className={`text-xs font-semibold uppercase tracking-wider ${
                    plan.highlight ? "text-brand-green-light" : "text-brand-green"
                  }`}
                >
                  Direct payments
                </p>
                <p
                  className={`mt-1 text-lg font-bold ${
                    plan.highlight ? "text-white" : "text-ink"
                  }`}
                >
                  {plan.directCap}
                  <span className="text-sm font-normal"> a month</span>
                </p>
              </div>

              <ul className="mt-6 flex-1 space-y-3">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className={`flex gap-2.5 text-sm leading-relaxed ${
                      plan.highlight ? "text-white/85" : "text-ink-muted"
                    }`}
                  >
                    <span
                      aria-hidden
                      className={plan.highlight ? "text-brand-green-light" : "text-brand-green"}
                    >
                      ✓
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.tier === "FREE" ? routes.signUp : routes.contact}
                className={`mt-8 rounded-lg px-5 py-3 text-center text-sm font-semibold transition-colors ${
                  plan.highlight
                    ? "bg-brand-green text-white hover:bg-brand-green-dark"
                    : "bg-brand-blue text-white hover:bg-brand-blue-light"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </Section>

      {/* THE CAP, EXPLAINED. Without this a supplier reads "R10,000" as a
        ceiling on their business and stops reading. */}
      <Section tone="wash" width="narrow">
          <h2 className="text-2xl font-bold tracking-tight text-brand-blue">
            What the monthly limit actually counts
          </h2>
          <div className="mt-5 space-y-4 leading-relaxed text-ink-muted">
            <p>
              It counts only <strong className="text-ink">direct payments</strong> — money that
              moves outside TruConnect. Cash on delivery, an EFT, a bank deposit. We never see any
              of it, and that is precisely why there is a limit on it.
            </p>
            <p>
              The limit exists for the same reason a bank asks where money came from. A platform
              that lets unlimited untraceable value move through it is a platform that gets used
              for something other than groceries, and we would rather be boring about this than
              explain it later.
            </p>
            <p>
              Card and instant EFT payments are coming, and they will not count against this
              limit — once the money moves through the platform it is already traceable, so there
              is nothing for a cap to protect against.
            </p>
            <p className="text-sm">
              Going over does not switch anything off mid-order. You get a warning as you
              approach it, and a conversation before anything changes.
            </p>
          </div>
      </Section>

      <Section>
        <div className="rounded-2xl border border-line/70 bg-white p-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-brand-blue sm:text-3xl">
            Not sure which fits?
          </h2>
          <p className="mx-auto mt-4 max-w-xl leading-relaxed text-ink-muted">
            Tell us roughly how many products you carry and how you keep your prices, and we will
            tell you honestly whether TruConnect is worth your time yet.
          </p>
          <Link
            href={routes.contact}
            className="mt-8 inline-flex rounded-lg bg-brand-blue px-7 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-blue-light"
          >
            Talk to sales
          </Link>
        </div>
      </Section>
    </>
  );
}
