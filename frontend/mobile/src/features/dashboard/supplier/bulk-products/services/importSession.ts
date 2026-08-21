/**
 * importSession.ts — carries the parsed spreadsheet + image manifest
 * from ImportUploadScreen to ImportPreviewScreen. Module-scoped state,
 * not Zustand/Context -- same comfort with simple module state this
 * codebase already uses (every mock API's own `let` array), and it's
 * the right amount of machinery for a value that's set once, read
 * once, by two screens in one linear flow. Not reactive on purpose:
 * Preview only ever mounts immediately after Upload finishes parsing,
 * so the data is guaranteed fresh by the time it reads this.
 *
 * ALSO CARRIES THE RAW PICKED FILES (spreadsheetFile/zipFile), NOT
 * JUST THE PARSED RESULT -- the client's own parse is for instant
 * preview only; the real backend re-parses and re-validates the
 * ACTUAL file independently (never trusts the client's own read), so
 * Confirm needs the original file references to actually upload, not
 * the derived rows.
 */

import type { ImportImageManifest, ParsedImportFile } from "../types";

export interface PickedFile {
  uri: string;
  name: string;
}

export interface ImportSession {
  file: ParsedImportFile;
  manifest: ImportImageManifest | null;
  spreadsheetFile: PickedFile;
  zipFile: PickedFile | null;
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
