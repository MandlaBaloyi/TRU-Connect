/**
 * ImportPreviewScreen — the real parsed rows, real errors, real
 * counts. Reads from importSession.ts (set by ImportUploadScreen just
 * before navigating here) rather than re-parsing or accepting route
 * params -- thousands of rows have no business round-tripping through
 * a URL.
 *
 * CONFIRM IS NOT WIRED TO A REAL IMPORT YET -- there is no backend
 * endpoint to send this to (Progress/Result/History are the next
 * slice). The button stays visible and honest about that rather than
 * either being hidden (which would make this feel unfinished for no
 * reason -- everything up to here is completely real) or silently
 * pretending to succeed (which would be a real lie about a
 * consequential action). Same "no silent dead taps" discipline as
 * ProductDetailScreen's own Edit button while it was unwired.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { getImportSession } from "../services/importSession";
import { computePreviewSummary } from "../algorithms/importCrossReference";
import { ImportPreviewRow } from "../components/ImportPreviewRow";
import { ImportSummaryCard } from "../components/ImportSummaryCard";
import type { ParsedImportRow } from "../types";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export default function ImportPreviewScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [isSubmitting] = useState(false);

  const session = useMemo(() => getImportSession(), []);

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

  const { file, manifest } = session;
  const summary = computePreviewSummary(file, manifest);
  const hasZip = manifest !== null;

  const handleConfirm = () => {
    Alert.alert(
      "Not connected yet",
      "The import screens are ready, but publishing to TRU Connect needs the backend import endpoint, which isn't built yet. Everything you're seeing here -- the parsed rows, the validation, the image matching -- is real and will be exactly what gets sent once that's wired up.",
      [{ text: "OK" }]
    );
  };

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
            <Text style={[styles.rowsHeading, { color: theme.colors.onSurfaceVariant }]}>Rows</Text>
          </View>
        }
        renderItem={({ item }) => <ImportPreviewRow row={item} />}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
      />

      <View style={[styles.footer, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outline }]}>
        <Pressable
          onPress={handleConfirm}
          disabled={summary.validRows === 0 || isSubmitting}
          style={[
            styles.submit,
            { backgroundColor: summary.validRows > 0 ? theme.colors.primary : theme.colors.surfaceDisabled },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Import products"
        >
          {isSubmitting ? (
            <ActivityIndicator color={theme.colors.onPrimary} />
          ) : (
            <Text
              style={[
                styles.submitText,
                { color: summary.validRows > 0 ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled },
              ]}
            >
              Import {summary.validRows} {summary.validRows === 1 ? "Product" : "Products"}
            </Text>
          )}
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
  rowsHeading: { ...typography.bodySmall, fontWeight: "700", marginTop: spacing.sm },
  separator: { height: StyleSheet.hairlineWidth },
  footer: { borderTopWidth: StyleSheet.hairlineWidth, padding: spacing.md },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
});
