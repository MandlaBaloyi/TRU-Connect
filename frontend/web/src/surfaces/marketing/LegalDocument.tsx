import Link from "next/link";

import { Section } from "@/design-system/patterns/Section";
import { routes } from "@/config/routes";
import type { LegalDocument as LegalDocumentData } from "@/surfaces/marketing/legalContent";

/**
 * Renders a legal document -- Terms or Privacy -- as a readable page.
 *
 * Narrow measure, real heading hierarchy, and the "pending legal review"
 * notice pulled out as a callout so nobody mistakes a draft for the
 * final thing. The content itself comes from `legalContent.ts`, ported
 * verbatim from the mobile app.
 */
export function LegalDocument({ doc }: { doc: LegalDocumentData }) {
  return (
    <Section width="narrow" space="lg">
      <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
        Legal
      </p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight text-brand-blue sm:text-5xl">
        {doc.title}
      </h1>
      <p className="mt-3 text-sm text-ink-muted">{doc.metaLine}</p>

      <div className="mt-8 rounded-2xl border border-amber-300 bg-amber-50 px-5 py-4">
        <h2 className="text-sm font-bold text-amber-900">
          {doc.notice.heading}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-amber-900/90">
          {doc.notice.body}
        </p>
      </div>

      <div className="mt-12 space-y-10">
        {doc.sections.map((section) => (
          <section key={section.heading}>
            <h2 className="text-lg font-semibold text-brand-blue">
              {section.heading}
            </h2>
            <p className="mt-3 leading-relaxed text-ink-muted">{section.body}</p>
          </section>
        ))}
      </div>

      <p className="mt-14 border-t border-line/60 pt-6 text-sm text-ink-muted">
        See also{" "}
        <Link
          href={doc.title === "Privacy Policy" ? routes.terms : routes.privacy}
          className="font-semibold text-brand-blue hover:text-brand-green"
        >
          {doc.title === "Privacy Policy"
            ? "Terms of Service"
            : "Privacy Policy"}
        </Link>
        .
      </p>
    </Section>
  );
}
