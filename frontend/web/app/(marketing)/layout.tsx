import { SiteFooter } from "@/surfaces/marketing/SiteFooter";
import { SiteHeader } from "@/surfaces/marketing/SiteHeader";

/**
 * The PUBLIC site shell: header, content, footer.
 *
 * Everything in this group is unauthenticated and statically generated,
 * because it exists to be found by search engines and read by someone
 * who has never heard of TruConnect. Nothing here may import from
 * (portal) or (auth) -- if a page needs a signed-in user, it is in the
 * wrong group.
 */
export default function MarketingLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">{children}</main>
      <SiteFooter />
    </>
  );
}
