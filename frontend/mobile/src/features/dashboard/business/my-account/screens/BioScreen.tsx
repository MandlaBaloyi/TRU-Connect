import React, { useState } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";
import { TextInput, useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Hero } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { MessageSquareText } from "lucide-react-native";

import { useBio } from "../hooks/useBio";
import { BIO_MAX_LENGTH } from "../types";

/**
 * file.txt §4 "ABOUT": keep this small, a reasonable character limit,
 * never a social-media biography. 140 characters — long enough for one
 * genuine sentence, short enough that it can't drift into a bio wall.
 */
export default function BioScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { bio: savedBio, save, isSaving } = useBio();

  const [value, setValue] = useState(savedBio ?? "");
  const remaining = BIO_MAX_LENGTH - value.length;

  const handleSave = async () => {
    await save(value);
    router.back();
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Hero
          icon={<MessageSquareText size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="About you"
          description="Tell customers and suppliers a little about your business."
        />
        <TextInput
          mode="outlined"
          value={value}
          onChangeText={(text) => setValue(text.slice(0, BIO_MAX_LENGTH))}
          multiline
          numberOfLines={3}
          placeholder="e.g. Independent retail business"
          autoFocus
        />
        <Text style={[styles.counter, { color: remaining < 0 ? theme.colors.error : theme.colors.onSurfaceVariant }]}>
          {remaining} characters left
        </Text>
        <PrimaryButton onPress={handleSave} loading={isSaving} disabled={isSaving}>
          Save
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  counter: { ...typography.bodySmall, textAlign: "right" },
});
