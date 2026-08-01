import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { Mail } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { OtpInput } from "@/components/forms/OtpInput";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useCountdown } from "@/hooks/useCountdown";
import { useRequestOtp, useVerifyOtp } from "@/features/auth/hooks/useOtp";
import { OTP_LENGTH, OTP_RESEND_SECONDS, STORAGE_KEYS } from "@/constants/config";
import { secureStorage } from "@/services/storage/secureStorage";
import { ApiError } from "@/services/api/apiClient";
import { spacing } from "@/theme/spacing";

/**
 * OTP Verification screen.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §2
 *
 * IMPORTANT: this screen does NOT request an OTP on mount. Registration
 * already sends the first code (AuthService._send_verification_otp), so
 * requesting another here would both consume one of the 5-per-hour rate
 * limited sends and invalidate the code already in the user's inbox --
 * the backend only treats the most recently issued code as valid.
 *
 * Only the explicit "Resend Code" action requests a new one.
 */
export default function VerifyOtpScreen() {
  const theme = useTheme();
  const [code, setCode] = useState("");
  const [destination, setDestination] = useState<string | null>(null);

  const { secondsLeft, isFinished, reset } = useCountdown(OTP_RESEND_SECONDS);
  const requestOtp = useRequestOtp();
  const verifyOtp = useVerifyOtp();

  useEffect(() => {
    secureStorage.getItem(STORAGE_KEYS.PENDING_VERIFICATION_EMAIL).then(setDestination);
  }, []);

  const handleResend = () => {
    if (!destination || requestOtp.isPending) return;
    requestOtp.mutate(destination);
    reset();
  };

  const handleVerify = () => {
    if (!destination) return;
    verifyOtp.mutate({ destination, code });
  };

  const errorMessage =
    verifyOtp.error instanceof ApiError
      ? verifyOtp.error.message
      : verifyOtp.isError
      ? "That code didn't work. Please try again."
      : null;

  return (
    <ScreenContainer>
      <View style={styles.iconWrap}>
        <Mail size={56} color={theme.colors.primary} />
      </View>

      <Text variant="headlineSmall" style={styles.title}>
        Verify Your Email
      </Text>
      <Text style={styles.description}>
        Enter the {OTP_LENGTH}-digit code we sent to{"\n"}
        <Text style={styles.destination}>{destination ?? "your email address"}</Text>
      </Text>

      <OtpInput value={code} onChange={setCode} length={OTP_LENGTH} />

      {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

      {requestOtp.isSuccess && !errorMessage && (
        <Text style={styles.infoText}>A new code has been sent.</Text>
      )}

      <Text
        style={[styles.resend, isFinished ? styles.resendActive : styles.resendInactive]}
        onPress={isFinished && destination ? handleResend : undefined}
      >
        {isFinished
          ? requestOtp.isPending
            ? "Sending..."
            : "Resend Code"
          : `Resend code in ${secondsLeft}s`}
      </Text>

      <PrimaryButton
        onPress={handleVerify}
        disabled={code.length !== OTP_LENGTH || !destination}
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
  destination: { fontWeight: "700", opacity: 1 },
  resend: { textAlign: "center", marginTop: spacing.md },
  resendActive: { fontWeight: "700" },
  resendInactive: { opacity: 0.5 },
  errorText: { color: "#D64545", textAlign: "center", marginTop: spacing.sm },
  infoText: { color: "#0FA968", textAlign: "center", marginTop: spacing.sm },
});