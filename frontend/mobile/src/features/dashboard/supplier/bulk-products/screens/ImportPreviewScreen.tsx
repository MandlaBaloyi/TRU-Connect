/**
 * ImportPreviewScreen — the real parsed rows, real errors, real
 * counts, AND NOW a real Confirm that actually submits to the backend
 * and polls for a real result. Reads from importSession.ts (set by
 * ImportUploadScreen just before navigating here) rather than
 * re-parsing or accepting route params -- thousands of rows have no
 * business round-tripping through a URL.
 *
 * FOUR STATES, ONE SCREEN -- PREVIEW (the original rows/errors view,
 * Confirm visible) -> SUBMITTING (uploading, brief) -> POLLING
 * (backend's own real job, re-parsed and re-validated server-side
 * independently of anything shown in PREVIEW) -> DONE (COMPLETED or
 * FAILED, final counts). Kept as one screen rather than a separate
 * route per state -- the transition is linear and this session's data
 * (session, job) is naturally shared across all four without needing
 * to thread it through navigation params.
 *
 * POLLING, NOT A WEBSOCKET -- matches the "202 Accepted, poll for
 * status" pattern the backend's own routes are built around. Every 2
 * seconds is frequent enough to feel responsive for a job that's
 * usually done in seconds, without hammering the endpoint.
 */

import React, { useEffect, useRef, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CheckCircle2, XCircle } from "lucide-react-native";

import { getImportSession, clearImportSession } from "../services/importSession";
import { computePreviewSummary } from "../algorithms/importCrossReference";
import { submitImport, getImportJob, getImportJobErrors } from "../api/bulkImportApi";
import { ImportPreviewRow } from "../components/ImportPreviewRow";
import { ImportSummaryCard } from "../components/ImportSummaryCard";
import type { ImportJob, ImportJobError, ParsedImportRow } from "../types";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

type ScreenState = "PREVIEW" | "SUBMITTING" | "POLLING" | "DONE";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED"]);

export default function ImportPreviewScreen() {
  const router = useRouter();
  const theme = useTheme();

  const [state, setState] = useState<ScreenState>("PREVIEW");
  const [job, setJob] = useState<ImportJob | null>(null);
  const [jobErrors, setJobErrors] = useState<ImportJobError[]>([]);
  const [showErrors, setShowErrors] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const session = useRef(getImportSession()).current;

  useEffect(() => {
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, []);

  if (!session) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Nothing to preview -- go back and upload a spreadsheet first."
          onRetry={() => router.replace("/supplier/bulk-products/import")}
        />
      </ScreenContainer>
    );
  }

  const { file, manifest, spreadsheetFile, zipFile } = session;
  const summary = computePreviewSummary(file, manifest);
  const hasZip = manifest !== null;

  const startPolling = (jobId: string) => {
    pollTimer.current = setInterval(async () => {
      try {
        const latest = await getImportJob(jobId);
        setJob(latest);
        if (TERMINAL_STATUSES.has(latest.status)) {
          if (pollTimer.current) clearInterval(pollTimer.current);
          if (latest.errorRows > 0 || latest.status === "FAILED") {
            try {
              setJobErrors(await getImportJobErrors(jobId));
            } catch {
              // Errors are a nice-to-have detail here -- the summary
              // counts already tell the honest headline story even if
              // this follow-up call fails.
            }
          }
          setState("DONE");
        }
      } catch {
        if (pollTimer.current) clearInterval(pollTimer.current);
        setSubmitError("Lost connection while checking import progress. Pull down to check again from history.");
        setState("DONE");
      }
    }, POLL_INTERVAL_MS);
  };

  const handleConfirm = async () => {
    setSubmitError(null);
    setState("SUBMITTING");
    try {
      const created = await submitImport(spreadsheetFile, zipFile, file);
      setJob(created);
      if (TERMINAL_STATUSES.has(created.status)) {
        setState("DONE");
      } else {
        setState("POLLING");
        startPolling(created.id);
      }
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Couldn't start the import. Check your connection.");
      setState("PREVIEW");
    }
  };

  const handleDone = () => {
    clearImportSession();
    router.replace("/supplier/products");
  };

  if (state === "DONE" && job) {
    const succeeded = job.status === "COMPLETED";
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.resultWrap}>
          {succeeded ? (
            <CheckCircle2 size={48} color={theme.colors.primary} strokeWidth={1.75} />
          ) : (
            <XCircle size={48} color={theme.colors.error} strokeWidth={1.75} />
          )}
          <Text style={[styles.resultTitle, { color: theme.colors.onSurface }]}>
            {succeeded ? "Import complete" : "Import failed"}
          </Text>
          {job.failureReason && (
            <Text style={[styles.resultReason, { color: theme.colors.error }]}>{job.failureReason}</Text>
          )}
          <View style={styles.resultStats}>
            <Text style={[styles.resultStat, { color: theme.colors.onSurface }]}>
              {job.createdRows} of {job.totalRows} products created
            </Text>
            {job.hasImagesZip && (
              <Text style={[styles.resultStat, { color: theme.colors.onSurfaceVariant }]}>
                {job.imagesMatched} of {job.imagesTotal} photos uploaded
              </Text>
            )}
            {job.errorRows > 0 && (
              <Text style={[styles.resultStat, { color: theme.colors.error }]}>{job.errorRows} rows had errors</Text>
            )}
          </View>

          {jobErrors.length > 0 && (
            <Pressable onPress={() => setShowErrors((v) => !v)} accessibilityRole="button">
              <Text style={[styles.viewErrorsLink, { color: theme.colors.primary }]}>
                {showErrors ? "Hide error details" : "View error details"}
              </Text>
            </Pressable>
          )}
        </View>

        {showErrors && (
          <FlatList
            data={jobErrors}
            keyExtractor={(e, i) => `${e.rowNumber}-${e.field}-${i}`}
            contentContainerStyle={styles.errorList}
            renderItem={({ item }) => (
              <View style={styles.errorRow}>
                <Text style={[styles.errorRowNumber, { color: theme.colors.onSurfaceVariant }]}>
                  Row {item.rowNumber}
                </Text>
                <Text style={[styles.errorMessage, { color: theme.colors.error }]}>{item.message}</Text>
              </View>
            )}
          />
        )}

        <View style={[styles.footer, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outline }]}>
          <Pressable
            onPress={handleDone}
            style={[styles.submit, { backgroundColor: theme.colors.primary }]}
            accessibilityRole="button"
            accessibilityLabel="Done"
          >
            <Text style={[styles.submitText, { color: theme.colors.onPrimary }]}>Done</Text>
          </Pressable>
        </View>
      </ScreenContainer>
    );
  }

  if (state === "SUBMITTING" || state === "POLLING") {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.progressWrap}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.progressTitle, { color: theme.colors.onSurface }]}>
            {state === "SUBMITTING" ? "Uploading..." : "Importing your products..."}
          </Text>
          {job && (
            <Text style={[styles.progressDetail, { color: theme.colors.onSurfaceVariant }]}>
              {job.createdRows} of {job.totalRows || summary.validRows} done so far
            </Text>
          )}
          <Text style={[styles.progressHint, { color: theme.colors.onSurfaceVariant }]}>
            This can take a moment for larger files -- you can leave this screen and check back from Import History.
          </Text>
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <FlatList<ParsedImportRow>
        data={file.rows}
        keyExtractor={(row) => String(row.rowNumber)}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <View style={styles.header}>
            <ImportSummaryCard summary={summary} hasZip={hasZip} />
            {file.missingRequiredColumns.length > 0 && (
              <View style={[styles.fileErrorBox, { backgroundColor: theme.colors.errorContainer }]}>
                <Text style={[styles.fileErrorTitle, { color: theme.colors.error }]}>Missing required columns</Text>
                <Text style={[styles.fileErrorBody, { color: theme.colors.error }]}>
                  {file.missingRequiredColumns.join(", ")} — check you're using the current template.
                </Text>
              </View>
            )}
            {file.unrecognizedColumns.length > 0 && (
              <Text style={[styles.unrecognizedNote, { color: theme.colors.onSurfaceVariant }]}>
                Unrecognised column{file.unrecognizedColumns.length === 1 ? "" : "s"} ignored:{" "}
                {file.unrecognizedColumns.join(", ")}
              </Text>
            )}
            {submitError && <Text style={[styles.submitErrorText, { color: theme.colors.error }]}>{submitError}</Text>}
            <Text style={[styles.rowsHeading, { color: theme.colors.onSurfaceVariant }]}>Rows</Text>
          </View>
        }
        renderItem={({ item }) => <ImportPreviewRow row={item} />}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
      />

      <View style={[styles.footer, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outline }]}>
        <Pressable
          onPress={handleConfirm}
          disabled={summary.validRows === 0}
          style={[
            styles.submit,
            { backgroundColor: summary.validRows > 0 ? theme.colors.primary : theme.colors.surfaceDisabled },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Import products"
        >
          <Text
            style={[
              styles.submitText,
              { color: summary.validRows > 0 ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled },
            ]}
          >
            Import {summary.validRows} {summary.validRows === 1 ? "Product" : "Products"}
          </Text>
        </Pressable>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, paddingBottom: spacing.xxl * 2 },
  header: { gap: spacing.sm, marginBottom: spacing.sm },
  fileErrorBox: { borderRadius: radius.md, padding: spacing.md, gap: 4 },
  fileErrorTitle: { ...typography.body, fontWeight: "700" },
  fileErrorBody: { ...typography.bodySmall },
  unrecognizedNote: { ...typography.caption },
  submitErrorText: { ...typography.bodySmall },
  rowsHeading: { ...typography.bodySmall, fontWeight: "700", marginTop: spacing.sm },
  separator: { height: StyleSheet.hairlineWidth },
  footer: { borderTopWidth: StyleSheet.hairlineWidth, padding: spacing.md },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  progressWrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, padding: spacing.xl },
  progressTitle: { ...typography.h2 },
  progressDetail: { ...typography.body },
  progressHint: { ...typography.bodySmall, textAlign: "center" },
  resultWrap: { alignItems: "center", gap: spacing.sm, padding: spacing.xl },
  resultTitle: { ...typography.h2 },
  resultReason: { ...typography.bodySmall, textAlign: "center" },
  resultStats: { alignItems: "center", gap: 4, marginTop: spacing.sm },
  resultStat: { ...typography.body },
  viewErrorsLink: { ...typography.bodySmall, fontWeight: "700", marginTop: spacing.sm },
  errorList: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl, gap: spacing.sm },
  errorRow: { gap: 2 },
  errorRowNumber: { ...typography.caption, fontWeight: "700" },
  errorMessage: { ...typography.bodySmall },
});
