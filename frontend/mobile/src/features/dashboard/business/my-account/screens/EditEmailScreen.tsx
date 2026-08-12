import React from "react";
import { ScrollView, StyleSheet } from "react-native";
import { useRouter } from "expo-router";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Note } from "@/components/lists/CardListUI";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { spacing } from "@/theme/spacing";

import { ContactFieldForm } from "../components/ContactFieldForm";
import { useUpdateContactField } from "../hooks/useContactDetails";

export default function EditEmailScreen() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const mutation = useUpdateContactField();

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ContactFieldForm
          label="Email address"
          initialValue={user?.email ?? ""}
          keyboardType="email-address"
          onSave={async (value) => {
            await mutation.mutateAsync({ field: "email", value });
            router.back();
          }}
        />
        <Note>Changing your email may require you to verify the new address before it takes effect.</Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
});
