import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

/**
 * ARCHITECTURE BOUNDARIES ARE ENFORCED HERE, NOT DOCUMENTED AND HOPED FOR.
 *
 * The layers, and the one rule that defines them:
 *
 *   surfaces/  ──▶  domains/  ──▶  api/ + design-system/  ──▶  lib/ + config/
 *
 *   IMPORTS ONLY EVER POINT RIGHT.
 *
 * Why each edge exists:
 *
 *   design-system/ knows nothing about TruConnect. A Button that imports
 *   a catalogue type cannot be reused by the admin control centre, and
 *   that reuse is the entire reason the layer exists.
 *
 *   api/ is transport. The moment it imports a component, the
 *   cookie-versus-bearer decision stops living in one file.
 *
 *   domains/ is business logic with no layout. Catalogue rules are used
 *   by BOTH the supplier portal and (later) the admin match-review
 *   queue -- if domains reached into surfaces, admin would have to
 *   duplicate them.
 *
 *   surfaces/ compose. Two surfaces never import each other: if the
 *   portal and marketing genuinely need the same thing, it belongs in
 *   design-system/ or domains/, and having to move it is the point.
 *
 * This mirrors the backend, which AST-parses src/shared/finance/ and
 * fails the build when it imports outside an allowlist ("Finance is a
 * leaf"). A layered structure without enforcement degrades in about
 * three months; with it, it holds.
 *
 * Implemented with no-restricted-imports rather than a boundaries
 * plugin, deliberately -- zero new dependencies, and the rule is
 * readable by anyone who opens this file.
 */

const layerRule = (from, forbidden) => ({
  files: [`src/${from}/**/*.{ts,tsx}`],
  rules: {
    "no-restricted-imports": [
      "error",
      {
        patterns: forbidden.map((layer) => ({
          group: [`@/${layer}/*`, `@/${layer}`],
          message: `Architecture: src/${from}/ must not import from src/${layer}/. Imports point right: surfaces -> domains -> api + design-system -> lib. See the comment at the top of eslint.config.mjs.`,
        })),
      },
    ],
  },
});

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,

  // Leaf layers: know nothing about anything above them.
  layerRule("lib", ["surfaces", "domains", "api", "design-system", "config"]),
  layerRule("config", ["surfaces", "domains", "api", "design-system"]),

  // Layer 1: reusable across every surface, so it stays domain-free.
  layerRule("design-system", ["surfaces", "domains", "api"]),
  layerRule("api", ["surfaces", "domains", "design-system"]),

  // Layer 2: business logic, no presentation.
  layerRule("domains", ["surfaces"]),

  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
