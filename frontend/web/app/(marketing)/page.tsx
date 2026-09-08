import { Landing } from "@/surfaces/marketing/Landing";

/**
 * `/` -- the public landing page.
 *
 * Thin by design: the page body, its copy and its structure live in
 * `src/surfaces/marketing/Landing.tsx`. Route files in `app/` only wire
 * a URL to a surface.
 */
export default function HomePage() {
  return <Landing />;
}
