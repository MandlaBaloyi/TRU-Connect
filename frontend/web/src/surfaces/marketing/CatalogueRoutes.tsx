import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { Section } from "@/design-system/patterns/Section";
import { routes } from "@/config/routes";
import { INGESTION_PATHS } from "@/surfaces/marketing/siteContent";

/**
 * How a supplier's catalogue actually reaches TruConnect.
 *
 * THE SECTION A SERIOUS WHOLESALER READS FIRST, and the one the site was
 * missing. A distributor with 3,000 lines does not care what the app
 * looks like -- they care whether joining means retyping their
 * catalogue. If the page cannot answer that in ten seconds they leave,
 * and that is exactly the segment the business needs most.
 *
 * It is TruConnect's honest equivalent of the "connects to your entire
 * tech stack" section every platform company has. The difference is that
 * a platform with integrations lists logos, and this lists three doors
 * -- because three doors is what actually exists.
 *
 * THE THIRD ONE SAYS "TALK TO US" RATHER THAN "AVAILABLE", deliberately.
 * Direct system integration is real and designed, and it is not
 * self-serve: it needs a conversation about their ERP before anything is
 * connected. Labelling it "available" would produce a supplier who signs
 * up expecting a button and finds none.
 */
export function CatalogueRoutes({ tone = "wash" }: { tone?: "plain" | "wash" }) {
  return (
    <Section tone={tone} divide space="lg">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
          Getting your products in
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
          You do not retype your catalogue.
        </h2>
        <p className="mt-4 text-lg leading-relaxed text-ink-muted">
          Whatever you already have — a notebook, a spreadsheet, or a system your team runs — there
          is a way in that does not mean starting again.
        </p>
      </div>

      <ol className="mt-12 grid gap-6 lg:grid-cols-3">
        {INGESTION_PATHS.map((path, index) => (
          <li
            key={path.name}
            className="flex flex-col rounded-xl border border-line/70 bg-white p-7"
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-bold tracking-wider text-brand-green">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  path.status === "Available"
                    ? "bg-brand-green/10 text-brand-green-dark"
                    : "bg-brand-blue/10 text-brand-blue"
                }`}
              >
                {path.status}
              </span>
            </div>

            <h3 className="mt-4 text-lg font-semibold text-ink">{path.name}</h3>
            <p className="mt-1 text-sm font-medium text-brand-blue">{path.forWho}</p>
            <p className="mt-3 flex-1 text-sm leading-relaxed text-ink-muted">{path.body}</p>
          </li>
        ))}
      </ol>

      {/* THE BARCODE LINE IS A REAL INCENTIVE, not a feature boast. A
          barcode makes matching exact and instant, which costs the
          platform nothing and saves the supplier a review queue. Saying
          so plainly aligns their effort with ours. */}
      <div className="mt-10 rounded-xl border border-brand-green/30 bg-brand-green/5 p-6">
        <p className="text-sm leading-relaxed text-ink">
          <strong className="font-semibold">One column matters more than the rest.</strong>{" "}
          If your spreadsheet has barcodes, put them in. Every product with a barcode is matched to
          our catalogue exactly and instantly — which is what lets a business compare your price
          against another supplier&rsquo;s for the same item.
        </p>
      </div>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Link href={routes.contact} className={buttonClass()}>
          Talk to us about your catalogue
        </Link>
        <Link href={routes.pricing} className={buttonClass({ variant: "secondary" })}>
          See plans
        </Link>
      </div>
    </Section>
  );
}
