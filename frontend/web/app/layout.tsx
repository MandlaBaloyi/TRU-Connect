import type { Metadata } from "next";
import { Geist } from "next/font/google";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

/**
 * ROOT LAYOUT -- <html>, <body>, fonts, and nothing else.
 *
 * NO CHROME LIVES HERE, deliberately. An earlier version put the
 * marketing header and footer in this file, which meant the supplier
 * portal would have inherited them the moment it existed. Chrome belongs
 * to the route group that owns it: (marketing) gets the public site
 * header and footer, (auth) gets a bare centred shell, (portal) gets the
 * signed-in shell and its role guard.
 *
 * Keeping this file empty of surface concerns is what makes each group's
 * layout the ONE place its shell is decided.
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
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
