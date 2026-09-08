import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { PageHeading } from "@/design-system/primitives/PageHeading";
import { Section } from "@/design-system/patterns/Section";
import { routes } from "@/config/routes";
import { CONTACT_EMAIL } from "@/surfaces/marketing/siteContent";

/**
 * Contact.
 *
 * NO CONTACT FORM, DELIBERATELY. A form needs somewhere to send the
 * message, and there is no backend endpoint for that yet -- a form that
 * looks like it submits and does not is the same mistake as the sign-in
 * form that looked like it logged you in. This page routes each kind of
 * question to a channel that actually works today: the app for anything
 * about an account, the supplier portal for suppliers, and email for
 * everything else.
 *
 * `CONTACT_EMAIL` is empty until a real, monitored address exists. While
 * it is empty the page says how to reach us in the app rather than
 * offering a `mailto:` to nowhere.
 */
// Defined in siteContent, not here -- it is the one string the owner
// has to fill in, and having it in two files is how one of them gets
// filled and the other does not.

const CHANNELS = [
  {
    title: "You use the app",
    body: "Questions about an order, a payment or your account are fastest to answer from inside the app, where we can see the account you mean. Open Help & support from the menu.",
  },
  {
    title: "You supply, or want to",
    body: "Everything a supplier needs to set up lives in the supplier area. Start there, or sign in if you already have an account.",
    action: { label: "For suppliers", href: routes.suppliers },
  },
];

export function Contact() {
  return (
    <>
      <Section space="lg">
        <PageHeading
          eyebrow="Contact"
          title="Reach the right place first time."
          lead="Most questions are quickest to answer where the account lives. Here is where each kind goes."
        />
      </Section>

      <Section tone="wash" divide space="lg">
        <div className="grid gap-6 md:grid-cols-2">
          {CHANNELS.map((c) => (
            <div
              key={c.title}
              className="flex flex-col rounded-2xl bg-white p-7 shadow-sm ring-1 ring-line/60"
            >
              <h2 className="text-lg font-semibold text-brand-blue">
                {c.title}
              </h2>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-ink-muted">
                {c.body}
              </p>
              {c.action && (
                <Link
                  href={c.action.href}
                  className={`mt-5 self-start ${buttonClass({ variant: "secondary", size: "md" })}`}
                >
                  {c.action.label}
                </Link>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-2xl bg-white p-7 shadow-sm ring-1 ring-line/60">
          <h2 className="text-lg font-semibold text-brand-blue">
            Anything else
          </h2>
          {CONTACT_EMAIL ? (
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              Email us at{" "}
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="font-semibold text-brand-blue hover:text-brand-green"
              >
                {CONTACT_EMAIL}
              </a>
              . Press, partnerships and general questions all reach the same
              inbox.
            </p>
          ) : (
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              A public email address for press, partnerships and general
              questions is being set up. Until then, the fastest route for
              anything account-related is Help &amp; support inside the app.
            </p>
          )}
        </div>
      </Section>

      <Section space="lg">
        <PageHeading
          title="Are you a business or a supplier?"
          align="center"
          lead="If you run a shop, TruConnect is in the app. If you supply shops, it starts on the web."
        />
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link href={routes.suppliers} className={buttonClass()}>
            I&rsquo;m a supplier
          </Link>
          <Link
            href={routes.home}
            className={buttonClass({ variant: "secondary" })}
          >
            Back to the home page
          </Link>
        </div>
      </Section>
    </>
  );
}
