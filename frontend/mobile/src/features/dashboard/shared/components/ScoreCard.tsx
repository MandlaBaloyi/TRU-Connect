import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, ProgressBar, useTheme } from "react-native-paper";
import { TrendingUp, TrendingDown } from "lucide-react-native";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

interface ScoreCardProps {
  label: string;
  score: number;
  maxScore?: number;
  trendPercent?: number;
  footnote?: string;
}

/**
 * Generic score display -- backs both "Business Trust Score" and
 * "Supplier Quality Score". Deliberately generic/reusable rather than
 * business- or supplier-specific, since both dashboards need an
 * identically-shaped "our trust engine's score for you" card.
 * Ref: master prompt "Business Trust Score" / "Trust Engine Integration"
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (Business Health Score, Supplier
 * Reputation).
 */
export function ScoreCard({ label, score, maxScore = 100, trendPercent, footnote }: ScoreCardProps) {
  const theme = useTheme();
  const progress = Math.max(0, Math.min(1, score / maxScore));
  const isPositiveTrend = (trendPercent ?? 0) >= 0;

  return (
    <AppCard style={styles.card}>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {label}
      </Text>
      <View style={styles.scoreRow}>
        <Text variant="displaySmall" style={styles.scoreValue}>
          {score}
        </Text>
        {trendPercent !== undefined && (
          <View style={styles.trendRow}>
            {isPositiveTrend ? (
              <TrendingUp size={16} color={theme.colors.primary} />
            ) : (
              <TrendingDown size={16} color={theme.colors.error} />
            )}
            <Text
              variant="bodySmall"
              style={{ color: isPositiveTrend ? theme.colors.primary : theme.colors.error }}
            >
              {isPositiveTrend ? "+" : ""}
              {trendPercent}%
            </Text>
          </View>
        )}
      </View>
      <ProgressBar progress={progress} style={styles.progress} color={theme.colors.primary} />
      {footnote && (
        <Text variant="bodySmall" style={[styles.footnote, { color: theme.colors.onSurfaceVariant }]}>
          {footnote}
        </Text>
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.md },
  scoreRow: { flexDirection: "row", alignItems: "flex-end", gap: spacing.sm, marginTop: spacing.xs },
  scoreValue: { fontWeight: "700" },
  trendRow: { flexDirection: "row", alignItems: "center", gap: 2, marginBottom: spacing.xs },
  progress: { height: 6, borderRadius: 3, marginTop: spacing.sm },
  footnote: { marginTop: spacing.xs },
});
