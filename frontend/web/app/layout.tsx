import type { Metadata } from "next";
import { Geist } from "next/font/google";

import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

/**
 * ROOT LAYOUT -- currently the PUBLIC layout, and that is a temporary
 * simplification worth flagging rather than hiding.
 *
 * The header and footer live here because every route on the site today
 * is public marketing. They do NOT belong on the supplier portal or the
 * admin control centre. When those land, this file keeps only <html>,
 * <body>, and the font, and the marketing chrome moves into a
 * (marketing) route group beside (portal) and (admin) -- the same route
 * group pattern the mobile app already uses for (auth) and (dashboard).
 *
 * Doing that split NOW would mean creating two empty groups to hold one
 * real one, so it waits until there is a second audience to separate.
 */
export const metadata: Metadata = {
  metadataBase: new URL("https://truconnect.co.za"),
  title: {
    default: "TruConnect — the supply network for independent businesses",
    template: "%s — TruConnect",
  },
  description:
    "TruConnect connects South Africa's spaza shops, salons and small retailers with the suppliers who stock them. Real prices, real stock, and a record of every order.",
  openGraph: {
    title: "TruConnect — the supply network for independent businesses",
    description:
      "Find suppliers, compare real prices, and order stock from your phone. Suppliers reach the shops already buying what they sell.",
    locale: "en_ZA",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en-ZA" className={`${geistSans.variable} h-full`}>
      <body className="flex min-h-full flex-col">
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
