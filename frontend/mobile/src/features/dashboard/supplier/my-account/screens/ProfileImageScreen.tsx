import React, { useEffect } from "react";
import { Alert, ScrollView, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Camera, Image as ImageIcon, Trash2 } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Card, CardSection, Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useFileUpload } from "../hooks/useFileUpload";
import { useProfileImage } from "../hooks/useProfileImage";
import { FileUploadStateView } from "../components/FileUploadStateView";

/**
 * file.txt §5: take photo / choose from gallery / remove photo, a real
 * preview before upload, cancel support, and the full uploading ->
 * processing -> approved/failed/retry sequence — never "upload
 * finished" presented as "security-approved" (that distinction lives
 * in FileUploadStateView, shared with the payment-proof flow).
 */
export default function ProfileImageScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { asset, progressPercent, errorMessage, pick, upload, cancel, remove, retry } = useFileUpload();
  const { profileImage, setProfileImage } = useProfileImage();

  // Once a fresh upload is approved, it becomes the account's profile
  // image — a deliberate, single point where that happens.
  useEffect(() => {
    if (asset && asset.status === "approved") {
      setProfileImage(asset).then(() => {
        router.back();
      });
    }
  }, [asset?.status]);

  const confirmRemoveExisting = () => {
    Alert.alert("Remove profile photo", "Remove your current profile photo?", [
      { text: "Cancel", style: "cancel" },
      { text: "Remove", style: "destructive", onPress: () => setProfileImage(null).then(() => router.back()) },
    ]);
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {asset ? (
          <>
            <FileUploadStateView
              asset={asset}
              progressPercent={progressPercent}
              onCancel={cancel}
              onRemove={remove}
              onRetry={retry}
            />
            {asset.status === "selected" && (
              <PrimaryButton onPress={upload}>Upload</PrimaryButton>
            )}
            {errorMessage && <Text style={[styles.error, { color: theme.colors.error }]}>{errorMessage}</Text>}
          </>
        ) : (
          <>
            <CardSection>
              <Card icon={(c) => <Camera size={20} color={c} />} label="Take photo" onPress={() => pick("CAMERA")} />
              <Card
                icon={(c) => <ImageIcon size={20} color={c} />}
                label="Choose from gallery"
                onPress={() => pick("LIBRARY")}
              />
              {profileImage && (
                <Card
                  tone="danger"
                  icon={(c) => <Trash2 size={20} color={c} />}
                  label="Remove current photo"
                  onPress={confirmRemoveExisting}
                />
              )}
            </CardSection>
            {errorMessage && <Text style={[styles.error, { color: theme.colors.error }]}>{errorMessage}</Text>}
            <Note>
              Your photo is reviewed before it appears on your profile. This can take a moment — you'll see its
              status here.
            </Note>
          </>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  error: { ...typography.bodySmall },
});
