/**
 * ImportUploadScreen — pick a spreadsheet (required) and an images ZIP
 * (optional -- per the original design principle: "don't let images
 * block products"), then parse both for real and hand off to
 * ImportPreviewScreen via importSession.ts.
 *
 * Parsing happens HERE, on Continue, not on Preview mount -- Preview
 * should never need to know how to read a file, only how to display
 * an already-parsed one. Errors from a genuinely broken/corrupt file
 * (wrong format, unreadable ZIP) surface here, inline, before ever
 * navigating away.
 */

import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import * as DocumentPicker from "expo-document-picker";
import { CheckCircle2, FileSpreadsheet, FileText, FolderArchive } from "lucide-react-native";

import { downloadImportGuide, downloadImportTemplate } from "../services/downloadDocuments";
import { parseSpreadsheetFile } from "../services/parseSpreadsheet";
import { parseImageManifest } from "../services/parseImageManifest";
import { applyImageManifest } from "../algorithms/importCrossReference";
import { setImportSession, type PickedFile } from "../services/importSession";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const SPREADSHEET_MIME_TYPES = [
  "text/csv",
  "text/comma-separated-values",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
];
const ZIP_MIME_TYPES = ["application/zip", "application/x-zip-compressed", "multipart/x-zip"];

export default function ImportUploadScreen() {
  const router = useRouter();
  const theme = useTheme();

  const [spreadsheetFile, setSpreadsheetFile] = useState<PickedFile | null>(null);
  const [zipFile, setZipFile] = useState<PickedFile | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<"template" | "guide" | null>(null);

  const pickSpreadsheet = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: SPREADSHEET_MIME_TYPES });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    setSpreadsheetFile({ uri: asset.uri, name: asset.name });
    setError(null);
  };

  const pickZip = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: ZIP_MIME_TYPES });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    setZipFile({ uri: asset.uri, name: asset.name });
    setError(null);
  };

  const handleDownload = async (kind: "template" | "guide") => {
    setIsDownloading(kind);
    try {
      if (kind === "template") await downloadImportTemplate();
      else await downloadImportGuide();
    } catch {
      setError("Couldn't open the download. Try again.");
    } finally {
      setIsDownloading(null);
    }
  };

  const handleContinue = async () => {
    if (!spreadsheetFile) return;
    setIsParsing(true);
    setError(null);
    try {
      const parsedFile = await parseSpreadsheetFile(spreadsheetFile.uri, spreadsheetFile.name);
      const manifest = zipFile ? await parseImageManifest(zipFile.uri, zipFile.name) : null;
      const withImageErrors = applyImageManifest(parsedFile, manifest);
      setImportSession({ file: withImageErrors, manifest, spreadsheetFile, zipFile });
      router.push("/supplier/bulk-products/import/preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't read that file. Check the format and try again.");
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>New here?</Text>
          <View style={styles.downloadRow}>
            <Pressable
              onPress={() => handleDownload("template")}
              disabled={isDownloading !== null}
              style={[styles.downloadLink, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Download import template"
            >
              {isDownloading === "template" ? (
                <ActivityIndicator size="small" color={theme.colors.primary} />
              ) : (
                <FileSpreadsheet size={16} color={theme.colors.primary} strokeWidth={2} />
              )}
              <Text style={[styles.downloadLinkText, { color: theme.colors.primary }]}>Download template</Text>
            </Pressable>
            <Pressable
              onPress={() => handleDownload("guide")}
              disabled={isDownloading !== null}
              style={[styles.downloadLink, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Download guide"
            >
              {isDownloading === "guide" ? (
                <ActivityIndicator size="small" color={theme.colors.primary} />
              ) : (
                <FileText size={16} color={theme.colors.primary} strokeWidth={2} />
              )}
              <Text style={[styles.downloadLinkText, { color: theme.colors.primary }]}>Download guide</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Spreadsheet</Text>
          <Pressable
            onPress={pickSpreadsheet}
            style={[styles.picker, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Choose spreadsheet file"
          >
            {spreadsheetFile ? (
              <CheckCircle2 size={20} color={theme.colors.primary} strokeWidth={2} />
            ) : (
              <FileSpreadsheet size={20} color={theme.colors.onSurfaceVariant} strokeWidth={1.75} />
            )}
            <View style={styles.pickerBody}>
              <Text style={[styles.pickerTitle, { color: theme.colors.onSurface }]} numberOfLines={1}>
                {spreadsheetFile ? spreadsheetFile.name : "Choose a .csv or .xlsx file"}
              </Text>
              <Text style={[styles.pickerHint, { color: theme.colors.onSurfaceVariant }]}>Required</Text>
            </View>
          </Pressable>
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Photos (optional)</Text>
          <Pressable
            onPress={pickZip}
            style={[styles.picker, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Choose images ZIP file"
          >
            {zipFile ? (
              <CheckCircle2 size={20} color={theme.colors.primary} strokeWidth={2} />
            ) : (
              <FolderArchive size={20} color={theme.colors.onSurfaceVariant} strokeWidth={1.75} />
            )}
            <View style={styles.pickerBody}>
              <Text style={[styles.pickerTitle, { color: theme.colors.onSurface }]} numberOfLines={1}>
                {zipFile ? zipFile.name : "Choose a .zip of product photos"}
              </Text>
              <Text style={[styles.pickerHint, { color: theme.colors.onSurfaceVariant }]}>
                Products publish without a photo if you skip this
              </Text>
            </View>
          </Pressable>
        </View>

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <Pressable
          onPress={handleContinue}
          disabled={!spreadsheetFile || isParsing}
          style={[
            styles.submit,
            { backgroundColor: spreadsheetFile ? theme.colors.primary : theme.colors.surfaceDisabled },
          ]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !spreadsheetFile || isParsing }}
          accessibilityLabel="Continue"
        >
          {isParsing ? (
            <ActivityIndicator color={theme.colors.onPrimary} />
          ) : (
            <Text
              style={[
                styles.submitText,
                { color: spreadsheetFile ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled },
              ]}
            >
              Continue
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  downloadRow: { flexDirection: "row", gap: spacing.sm },
  downloadLink: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minHeight: 44,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  downloadLinkText: { ...typography.bodySmall, fontWeight: "600" },
  picker: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    minHeight: 64,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  pickerBody: { flex: 1, gap: 2 },
  pickerTitle: { ...typography.body, fontWeight: "600" },
  pickerHint: { ...typography.caption },
  error: { ...typography.bodySmall },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
});
