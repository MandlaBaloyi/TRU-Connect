import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { Smartphone } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { OtpInput } from "@/components/forms/OtpInput";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useCountdown } from "@/hooks/useCountdown";
import { useRequestOtp, useVerifyOtp } from "@/features/auth/hooks/useOtp";
import { OTP_LENGTH, OTP_RESEND_SECONDS } from "@/constants/config";
import { spacing } from "@/theme/spacing";

/**
 * OTP Verification screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 6) and
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Verification).
 */
export default function VerifyOtpScreen() {
  const theme = useTheme();
  const [code, setCode] = useState("");
  const { secondsLeft, isFinished, reset } = useCountdown(OTP_RESEND_SECONDS);
  const requestOtp = useRequestOtp();
  const verifyOtp = useVerifyOtp();

  const handleResend = () => {
    requestOtp.mutate("current-user-destination");
    reset();
  };

  const handleVerify = () => {
    verifyOtp.mutate({ destination: "current-user-destination", code });
  };

  return (
    <ScreenContainer>
      <View style={styles.iconWrap}>
        <Smartphone size={56} color={theme.colors.primary} />
      </View>

      <Text variant="headlineSmall" style={styles.title}>
        Verify Your Number
      </Text>
      <Text style={styles.description}>
        Enter the {OTP_LENGTH}-digit verification code sent to your phone.
      </Text>

      <OtpInput value={code} onChange={setCode} length={OTP_LENGTH} />

      {verifyOtp.isError && (
        <Text style={styles.errorText}>That code didn't work. Please try again.</Text>
      )}

      <Text
        style={[styles.resend, isFinished ? styles.resendActive : styles.resendInactive]}
        onPress={isFinished ? handleResend : undefined}
      >
        {isFinished ? "Resend Code" : `Resend code in ${secondsLeft}s`}
      </Text>

      <PrimaryButton
        onPress={handleVerify}
        disabled={code.length !== OTP_LENGTH}
        loading={verifyOtp.isPending}
        style={{ marginTop: spacing.lg }}
      >
        Verify
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  iconWrap: { alignItems: "center", marginTop: spacing.xl },
  title: { fontWeight: "700", textAlign: "center", marginTop: spacing.lg },
  description: { textAlign: "center", opacity: 0.7, marginTop: spacing.sm },
  resend: { textAlign: "center", marginTop: spacing.md },
  resendActive: { fontWeight: "700" },
  resendInactive: { opacity: 0.5 },
  errorText: { color: "#D64545", textAlign: "center", marginTop: spacing.sm },
});
