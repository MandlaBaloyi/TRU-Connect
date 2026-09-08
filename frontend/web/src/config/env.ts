/**
 * Environment configuration, read once and validated here rather than
 * scattered through the codebase as bare process.env reads.
 *
 * NEXT_PUBLIC_ IS A DECLARATION, NOT A CONVENIENCE. Anything with that
 * prefix is inlined into the browser bundle at build time and is
 * therefore public. Never put a secret behind one -- server-only values
 * belong in a plain env var read inside a route handler or server
 * component, where the bundle never sees them.
 */

/** The Flask API. Same backend the mobile app talks to. */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000/api/v1";

/**
 * Cloudinary cloud name -- public by design. Marketing and catalogue
 * imagery is delivered straight from Cloudinary so it can be replaced
 * and re-transformed without a deploy. The API SECRET is never here; it
 * stays on the backend, which is what signs uploads.
 */
export const CLOUDINARY_CLOUD_NAME =
  process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME ?? "";
