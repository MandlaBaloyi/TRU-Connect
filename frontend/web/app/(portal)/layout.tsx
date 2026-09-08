import { PortalHeader } from "@/surfaces/portal/PortalHeader";

/**
 * The signed-in shell.
 *
 * NO SESSION CHECK HERE, and that is not an oversight. The session
 * lives in an httpOnly cookie, so the only way to learn who the viewer
 * is, is to ask the backend -- and doing that in a layout would either
 * make every portal page a server round-trip before it renders, or
 * duplicate the check the page already has to do to get the user's
 * details anyway. The page owns the gate; this owns the frame.
 *
 * WORTH SAYING PLAINLY: a client-side redirect is a redirect for the
 * PERSON, never a security boundary. Nothing here protects data. What
 * protects data is that every endpoint behind this screen requires the
 * cookie and re-checks the account in the database on each request
 * (@fully_authenticated). If this gate were removed entirely, a
 * signed-out visitor would see an empty page, not somebody's catalogue.
 */
export default function PortalLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-screen flex-col bg-wash">
      <PortalHeader />
      <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-12">{children}</main>
    </div>
  );
}
