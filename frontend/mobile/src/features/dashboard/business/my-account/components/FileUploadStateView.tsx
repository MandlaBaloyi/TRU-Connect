/**
 * Renders whatever state a FileAsset is currently in. ONE
 * implementation shared by the profile-image and payment-proof
 * screens — see fileRepository.ts's docstring on why that sharing
 * matters here specifically.
 *
 * Every branch below uses a SAFE, generic message — never a
 * scanner/parser detail (file.txt §7). "processing" deliberately says
 * "Checking file..." rather than anything implying a specific check
 * (virus scan, magic-byte check, etc.) actually ran, because none of
 * that is real yet.
 */
import React from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { AlertTriangle, CheckCircle2, FileText, X } from "lucide-react-native";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import type { FileAsset } from "../types";

interface Props {
  asset: FileAsset;
  progressPercent: number;
  onCancel?: () => void;
  onRemove?: () => void;
  onRetry?: () => void;
}

export function FileUploadStateView({ asset, progressPercent, onCancel, onRemove, onRetry }: Props) {
  const theme = useTheme();
  const previewUri = asset.kind === "IMAGE" ? asset.localUri : null;

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
      <View style={styles.row}>
        {previewUri ? (
          <Image source={{ uri: previewUri }} style={styles.thumb} />
        ) : (
          <View style={[styles.thumb, styles.fileIconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
            <FileText size={22} color={theme.colors.onSurfaceVariant} />
          </View>
        )}

        <View style={styles.info}>
          <Text style={[styles.fileName, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {asset.fileName}
          </Text>
          <StatusLine asset={asset} progressPercent={progressPercent} />
        </View>

        {(asset.status === "selected" || asset.status === "approved" || asset.status === "rejected" || asset.status === "failed") &&
          onRemove && (
            <Pressable onPress={onRemove} accessibilityRole="button" accessibilityLabel="Remove file" hitSlop={8}>
              <X size={18} color={theme.colors.onSurfaceVariant} />
            </Pressable>
          )}
      </View>

      {asset.status === "uploading" && (
        <View style={[styles.progressTrack, { backgroundColor: theme.colors.surfaceVariant }]}>
          <View
            style={[styles.progressFill, { backgroundColor: theme.colors.primary, width: `${progressPercent}%` }]}
          />
        </View>
      )}

      {asset.status === "uploading" && onCancel && (
        <Text onPress={onCancel} style={[styles.cancelLink, { color: theme.colors.error }]} accessibilityRole="button">
          Cancel
        </Text>
      )}

      {(asset.status === "rejected" || asset.status === "failed") && onRetry && (
        <PrimaryButton onPress={onRetry} style={styles.retryButton}>
          Try another file
        </PrimaryButton>
      )}
    </View>
  );
}

function StatusLine({ asset, progressPercent }: { asset: FileAsset; progressPercent: number }) {
  const theme = useTheme();

  switch (asset.status) {
    case "selected":
      return <Text style={[styles.status, { color: theme.colors.onSurfaceVariant }]}>Ready to upload</Text>;
    case "uploading":
      return (
        <View style={styles.statusRow}>
          <ActivityIndicator size="small" color={theme.colors.primary} />
          <Text style={[styles.status, { color: theme.colors.onSurfaceVariant }]}>
            Uploading... {progressPercent}%
          </Text>
        </View>
      );
    case "processing":
      return (
        <View style={styles.statusRow}>
          <ActivityIndicator size="small" color={theme.colors.primary} />
          <Text style={[styles.status, { color: theme.colors.onSurfaceVariant }]}>Checking file...</Text>
        </View>
      );
    case "approved":
      return (
        <View style={styles.statusRow}>
          <CheckCircle2 size={14} color={theme.colors.secondary} strokeWidth={2.4} />
          <Text style={[styles.status, { color: theme.colors.secondary, fontWeight: "700" }]}>Approved</Text>
        </View>
      );
    case "rejected":
    case "failed":
      return (
        <View style={styles.statusRow}>
          <AlertTriangle size={14} color={theme.colors.error} strokeWidth={2.4} />
          <Text style={[styles.status, { color: theme.colors.error }]}>
            This file could not be accepted. Please choose another file.
          </Text>
        </View>
      );
    case "cancelled":
      return <Text style={[styles.status, { color: theme.colors.onSurfaceVariant }]}>Cancelled</Text>;
    default:
      return null;
  }
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.md, gap: spacing.sm },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  thumb: { width: 48, height: 48, borderRadius: radius.md },
  fileIconWrap: { alignItems: "center", justifyContent: "center" },
  info: { flex: 1, gap: 2 },
  fileName: { ...typography.body, fontWeight: "600" },
  status: { ...typography.bodySmall },
  statusRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  progressTrack: { height: 6, borderRadius: radius.pill, overflow: "hidden" },
  progressFill: { height: "100%", borderRadius: radius.pill },
  cancelLink: { ...typography.bodySmall, fontWeight: "700", alignSelf: "flex-start" },
  retryButton: { marginTop: spacing.xs },
});
