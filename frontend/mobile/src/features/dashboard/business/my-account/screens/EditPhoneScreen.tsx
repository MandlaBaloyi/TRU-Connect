import React from "react";
import { ScrollView, StyleSheet } from "react-native";
import { useRouter } from "expo-router";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Note } from "@/components/lists/CardListUI";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { spacing } from "@/theme/spacing";

import { ContactFieldForm } from "../components/ContactFieldForm";
import { useUpdateContactField } from "../hooks/useContactDetails";

export default function EditPhoneScreen() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const mutation = useUpdateContactField();

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ContactFieldForm
          label="Phone number"
          initialValue={user?.phoneNumber ?? ""}
          keyboardType="phone-pad"
          onSave={async (value) => {
            await mutation.mutateAsync({ field: "phone", value });
            router.back();
          }}
        />
        <Note>Your phone number is used to sign in and for account recovery.</Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
});
