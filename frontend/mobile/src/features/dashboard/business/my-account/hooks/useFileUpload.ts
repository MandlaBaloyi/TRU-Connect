/**
 * Drives ONE file through select -> upload -> processing -> approved/
 * rejected/failed (types.ts's UploadStatus). Shared by both the
 * profile-image screen and the payment-proof screen — see
 * fileRepository.ts's own docstring on why this is one implementation,
 * not two.
 *
 * RACE-SAFETY (file.txt §12, §28's "tap upload twice" / "navigate away
 * while uploading" / "retry while previous request is still pending"):
 *   - `busyRef` blocks a second select/upload from starting while one
 *     is already in flight, independent of React re-render timing.
 *   - `generationRef` is bumped on cancel/unmount/replace; every
 *     progress callback checks it belongs to the CURRENT generation
 *     before touching state, so a stale in-flight upload from a
 *     previous selection (or a screen the user has since left) can
 *     never overwrite newer state.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  deleteFile,
  FileRepositoryError,
  selectFile,
  uploadFile,
  type SelectSource,
} from "../services/fileRepository";
import type { FileAsset } from "../types";

export function useFileUpload() {
  const [asset, setAsset] = useState<FileAsset | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const busyRef = useRef(false);
  const generationRef = useRef(0);

  useEffect(() => {
    return () => {
      // Invalidates any in-flight callbacks from this hook instance —
      // covers "navigate away while uploading" without needing a real
      // AbortController, since the mock repository is timer-driven.
      generationRef.current += 1;
    };
  }, []);

  const pick = useCallback(async (source: SelectSource) => {
    if (busyRef.current) return; // guards double-tap
    busyRef.current = true;
    setErrorMessage(null);
    try {
      const selected = await selectFile(source);
      setAsset(selected);
      setProgressPercent(0);
    } catch (e) {
      if (e instanceof FileRepositoryError && e.code === "CANCELLED") {
        // Silent — the person just closed the picker.
      } else if (e instanceof FileRepositoryError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Something went wrong selecting that file. Please try again.");
      }
    } finally {
      busyRef.current = false;
    }
  }, []);

  const upload = useCallback(async () => {
    if (busyRef.current || !asset || asset.status !== "selected") return;
    busyRef.current = true;
    const myGeneration = generationRef.current;
    setErrorMessage(null);

    try {
      const result = await uploadFile(asset, (session) => {
        if (generationRef.current !== myGeneration) return; // stale — dropped
        setAsset(session.asset);
        setProgressPercent(session.progressPercent);
      });
      if (generationRef.current !== myGeneration) return;
      setAsset(result);
    } catch {
      if (generationRef.current !== myGeneration) return;
      setAsset((current) => (current ? { ...current, status: "failed" } : current));
      setErrorMessage("This file could not be accepted. Please choose another file.");
    } finally {
      busyRef.current = false;
    }
  }, [asset]);

  const cancel = useCallback(() => {
    generationRef.current += 1; // drop any in-flight progress callbacks
    setAsset((current) => (current ? { ...current, status: "cancelled" } : current));
  }, []);

  const remove = useCallback(async () => {
    generationRef.current += 1;
    if (asset?.id) {
      try {
        await deleteFile(asset.id);
      } catch {
        // Best-effort — the local UI state clears regardless below.
      }
    }
    setAsset(null);
    setProgressPercent(0);
    setErrorMessage(null);
  }, [asset]);

  const retry = useCallback(() => {
    setAsset((current) => (current ? { ...current, status: "selected", statusMessage: null } : current));
    setErrorMessage(null);
  }, []);

  return { asset, progressPercent, errorMessage, pick, upload, cancel, remove, retry };
}
