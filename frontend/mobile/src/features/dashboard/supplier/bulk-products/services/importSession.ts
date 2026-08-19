/**
 * importSession.ts — carries the parsed spreadsheet + image manifest
 * from ImportUploadScreen to ImportPreviewScreen. Module-scoped state,
 * not Zustand/Context -- same comfort with simple module state this
 * codebase already uses (every mock API's own `let` array), and it's
 * the right amount of machinery for a value that's set once, read
 * once, by two screens in one linear flow. Not reactive on purpose:
 * Preview only ever mounts immediately after Upload finishes parsing,
 * so the data is guaranteed fresh by the time it reads this.
 */

import type { ImportImageManifest, ParsedImportFile } from "../types";

export interface ImportSession {
  file: ParsedImportFile;
  manifest: ImportImageManifest | null;
}

let currentSession: ImportSession | null = null;

export function setImportSession(session: ImportSession): void {
  currentSession = session;
}

export function getImportSession(): ImportSession | null {
  return currentSession;
}

export function clearImportSession(): void {
  currentSession = null;
}
