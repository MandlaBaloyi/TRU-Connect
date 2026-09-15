import React, { useEffect, useState } from "react";
import { StyleSheet, View, ScrollView } from "react-native";
import { Text, Checkbox, Divider, useTheme } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useLocalSearchParams, useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import {
  businessRegisterSchema,
  BusinessRegisterFormValues,
  supplierRegisterSchema,
  SupplierRegisterFormValues,
} from "@/features/auth/schemas/authSchemas";
import { useRegister, useGoogleSignIn } from "@/features/auth/hooks/useAuth";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import { ApiError, getErrorMessage } from "@/services/api/apiClient";
import type { UserRole } from "@/features/auth/types";
import { spacing } from "@/theme/spacing";
import { PolicyLinksText } from "@/components/legal/PolicyLinksText";

/**
 * Create Account screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 5)
 *
 * Five fixes here that were previously silent:
 *  1. register.isError was never read -- a duplicate-email 409 produced
 *     no feedback at all; the user just saw nothing happen.
 *  2. The Privacy Policy / Terms checkbox is validated by the Zod schema
 *     (z.literal(true)) but was never wrapped in anything that displays
 *     formState.errors -- so an unchecked box silently blocked
 *     submission with zero visible reason why.
 *  3. registerErrorMessage only recognized ApiError instances -- when
 *     authService.register() crashed with a plain TypeError (reading
 *     .tokens off a response that no longer has one, pre-hardening-fix),
 *     that check was too narrow to catch it, so the screen showed
 *     nothing even though the mutation had failed. getErrorMessage()
 *     always returns something displayable, for any error shape.
 *  4. `role` used to default to "business" synchronously while the real
 *     stored role loaded asynchronously in the background -- meaning
 *     the Business form always rendered first and confidently, then got
 *     silently swapped for Supplier a moment later if that's what was
 *     actually picked. Now `role` starts as null ("not yet known") and
 *     nothing renders until the real answer has loaded, so the wrong
 *     form is never painted even briefly.
 *
 *     A SECOND, related flash was found after fixing #4: because the
 *     form only mounts for the very first time once role resolves
 *     (rather than being present from frame one, like Sign In's form
 *     is), react-native-paper's outlined TextInput labels visibly
 *     settle into their final position on that first mount -- a normal
 *     library behavior that's invisible when a form is already on
 *     screen, but visible when 6 fields all mount together a moment
 *     after the screen itself appeared. `revealed` below masks exactly
 *     that one-time settling: the form mounts and lays out at
 *     opacity 0, and only becomes visible one frame later, once
 *     react-native-paper's labels have already finished settling
 *     off-screen.
 *  5. The role===null loading branch previously did `return null` --
 *     rendering LITERALLY NOTHING, no View, no background. That let the
 *     navigator's own default (unthemed, white) background show through
 *     for that brief window -- invisible in light mode (white matches),
 *     but a visible white flash in dark mode. Rendering an empty,
 *     correctly-themed <ScreenContainer /> instead means the right
 *     background paints immediately, even with nothing else on screen
 *     yet.
 *  6. role was ALWAYS resolved via an async secureStorage read, even
 *     when arriving straight from role-selection.tsx -- which already
 *     knew the role (the user had just picked it) and had already
 *     written it to storage a moment earlier. Re-reading it here was a
 *     redundant round-trip that produced a visible blank-screen gap
 *     between tapping Continue and the form actually appearing -- the
 *     real cause of the reported "delay". role-selection.tsx now passes
 *     the role directly as a route param, read synchronously below; the
 *     async read is now only a fallback for arriving without one.
 */
export default function CreateAccountScreen() {
  const register = useRegister();
  const googleSignIn = useGoogleSignIn();
  const params = useLocalSearchParams<{ role?: string; invitationTicket?: string }>();
  // If role-selection navigated here, the role is already known --
  // read directly from the route param (synchronous, no delay) rather
  // than the async secureStorage read below, which used to be the ONLY
  // source and was the real cause of a visible blank-screen gap
  // between "tap Continue" and the form actually appearing (that read
  // was re-fetching a value role-selection already had in hand and had
  // already written to storage a moment earlier -- a redundant
  // round-trip, not a necessary one). Falls back to secureStorage only
  // when arriving without a param (e.g. a direct deep link, or
  // returning here by some path other than role-selection's Continue).
  const paramRole: UserRole | null =
    params.role === "supplier" ? "supplier" : params.role === "business" ? "business" : null;
  // Supplier Invitation (file.txt Phase 2) -- present only when this
  // screen was reached via an invitation link (a deep link or a future
  // /join web page passing it through as a route param). Not a form
  // field the person edits; passed straight to the register call
  // untouched. See SupplierRegisterPayload's own docstring.
  const invitationTicket = params.invitationTicket || undefined;
  // null = "not yet determined" -- deliberately NOT defaulted to
  // "business". See docstring point 4.
  const [role, setRole] = useState<UserRole | null>(paramRole);
  // Masks the label-settling flash on the form's first-ever mount --
  // see docstring's second note. Reset per form-mount, not global.
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (paramRole) return; // already known synchronously -- no read needed
    secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE).then((stored) => {
      setRole(stored === "supplier" ? "supplier" : "business");
    });
  }, [paramRole]);

  const registerErrorMessage = register.isError
    ? getErrorMessage(register.error, "We couldn't create your account. Please try again.")
    : null;
  const isDuplicateEmail = register.error instanceof ApiError && register.error.status === 409;

  // Render a themed, empty background -- NEVER return null/nothing
  // here. See docstring point 5 for why.
  if (role === null) {
    return <ScreenContainer />;
  }

  return (
    <View
      style={{ flex: 1, opacity: revealed ? 1 : 0 }}
      onLayout={() => requestAnimationFrame(() => setRevealed(true))}
    >
      {role === "business" ? (
        <BusinessRegisterForm
          onSubmit={(values) => register.mutate({ role: "business", ...values })}
          isSubmitting={register.isPending}
          errorMessage={registerErrorMessage}
          isDuplicateEmail={isDuplicateEmail}
          onGooglePress={() => googleSignIn.mutate("")}
          isGoogleLoading={googleSignIn.isPending}
        />
      ) : (
        <SupplierRegisterForm
          onSubmit={(values) => register.mutate({ role: "supplier", ...values, invitationTicket })}
          isSubmitting={register.isPending}
          errorMessage={registerErrorMessage}
          isDuplicateEmail={isDuplicateEmail}
          onGooglePress={() => googleSignIn.mutate("")}
          isGoogleLoading={googleSignIn.isPending}
          invitationTicket={invitationTicket}
        />
      )}
    </View>
  );
}

interface CommonProps {
  onGooglePress: () => void;
  isGoogleLoading: boolean;
  errorMessage: string | null;
  isDuplicateEmail: boolean;
}

function RegisterError({ errorMessage, isDuplicateEmail }: Pick<CommonProps, "errorMessage" | "isDuplicateEmail">) {
  if (!errorMessage) return null;
  return (
    <View style={{ marginBottom: spacing.md }}>
      <Text style={styles.errorText}>{errorMessage}</Text>
      {isDuplicateEmail && (
        <Link href="/(auth)/sign-in">
          <Text style={styles.link}>Sign in instead</Text>
        </Link>
      )}
    </View>
  );
}

function BusinessRegisterForm({
  onSubmit,
  isSubmitting,
  errorMessage,
  isDuplicateEmail,
  onGooglePress,
  isGoogleLoading,
}: {
  onSubmit: (values: BusinessRegisterFormValues) => void;
  isSubmitting: boolean;
} & CommonProps) {
  const router = useRouter();
  const theme = useTheme();
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BusinessRegisterFormValues>({
    resolver: zodResolver(businessRegisterSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      businessName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptPrivacyPolicy: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptPrivacyPolicy");
  const toggleAccepted = () => setValue("acceptPrivacyPolicy", !accepted as unknown as true, { shouldValidate: true });

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineSmall" style={styles.title}>
          Create Your Business Account
        </Text>

        <RegisterError errorMessage={errorMessage} isDuplicateEmail={isDuplicateEmail} />

        <FormTextField control={control} name="firstName" label="First Name" />
        <FormTextField control={control} name="lastName" label="Last Name" />
        {/* NO LONGER OPTIONAL. This is the name every business-facing
            screen shows -- Find Business, an incoming connection
            request, the Community card -- and while it was optional it
            was also never persisted, so the fallback was the owner's
            own name on all three. */}
        <FormTextField control={control} name="businessName" label="Business Name" />
        <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        {/*
          Combined agreement, per direct feedback: the Terms of Service
          and Privacy Policy are two different documents doing two
          different jobs (rules of use vs. data handling), so accepting
          only one was never really sufficient — both are now covered
          by a single checkbox, and both document names are real
          tappable links to the public (legal) screens, not just plain
          text. The checkbox itself still toggles on tapping anywhere
          in the sentence EXCEPT the two links — those navigate
          instead, which is why they're nested Text elements with their
          own onPress rather than part of the same pressable block.
        */}
        <View style={styles.row}>
          <Checkbox status={accepted ? "checked" : "unchecked"} onPress={toggleAccepted} />
          <Text onPress={toggleAccepted} style={styles.agreementText}>
            I agree to TruConnect's{" "}
            <Text
              style={{ color: theme.colors.primary, fontWeight: "700" }}
              onPress={() => router.push("/(legal)/terms")}
              accessibilityRole="link"
            >
              Terms of Service
            </Text>{" "}
            and{" "}
            <Text
              style={{ color: theme.colors.primary, fontWeight: "700" }}
              onPress={() => router.push("/(legal)/privacy-policy")}
              accessibilityRole="link"
            >
              Privacy Policy
            </Text>
          </Text>
        </View>
        {errors.acceptPrivacyPolicy && (
          <Text style={styles.fieldError}>{errors.acceptPrivacyPolicy.message}</Text>
        )}

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton icon="google" onPress={onGooglePress} loading={isGoogleLoading} style={{ marginTop: spacing.md }}>
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

function SupplierRegisterForm({
  onSubmit,
  isSubmitting,
  errorMessage,
  isDuplicateEmail,
  onGooglePress,
  isGoogleLoading,
  invitationTicket,
}: {
  onSubmit: (values: SupplierRegisterFormValues) => void;
  isSubmitting: boolean;
  invitationTicket?: string;
} & CommonProps) {
  const router = useRouter();
  const theme = useTheme();
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SupplierRegisterFormValues>({
    resolver: zodResolver(supplierRegisterSchema),
    defaultValues: {
      businessName: "",
      ownerName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptTerms");
  const toggleAccepted = () => setValue("acceptTerms", !accepted as unknown as true, { shouldValidate: true });

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineSmall" style={styles.title}>
          Create Your Supplier Account
        </Text>

        {invitationTicket && (
          <Text style={styles.invitedNote}>You're joining via an invitation — you'll be connected automatically.</Text>
        )}

        <RegisterError errorMessage={errorMessage} isDuplicateEmail={isDuplicateEmail} />

        <FormTextField control={control} name="businessName" label="Business Name" />
        <FormTextField control={control} name="ownerName" label="Owner Name (optional)" />
        <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />
        <PasswordField control={control} name="password" label="Password" />
        <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

        {/* Same combined, clickable agreement as the business form —
            see its own comment for the full reasoning. */}
        <View style={styles.row}>
          <Checkbox status={accepted ? "checked" : "unchecked"} onPress={toggleAccepted} />
          <Text onPress={toggleAccepted} style={styles.agreementText}>
            I agree to TruConnect's{" "}
            <Text
              style={{ color: theme.colors.primary, fontWeight: "700" }}
              onPress={() => router.push("/(legal)/terms")}
              accessibilityRole="link"
            >
              Terms of Service
            </Text>{" "}
            and{" "}
            <Text
              style={{ color: theme.colors.primary, fontWeight: "700" }}
              onPress={() => router.push("/(legal)/privacy-policy")}
              accessibilityRole="link"
            >
              Privacy Policy
            </Text>
          </Text>
        </View>
        {errors.acceptTerms && <Text style={styles.fieldError}>{errors.acceptTerms.message}</Text>}

        <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
          Create Account
        </PrimaryButton>

        <Divider style={{ marginVertical: spacing.lg }} />
        <Text style={styles.orText}>OR</Text>

        <SecondaryButton icon="google" onPress={onGooglePress} loading={isGoogleLoading} style={{ marginTop: spacing.md }}>
          Continue with Google
        </SecondaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  scrollContent: { paddingBottom: spacing.xl },
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.xs },
  agreementText: { flex: 1, flexShrink: 1 },
  fieldError: { color: "#D64545", fontSize: 12, marginBottom: spacing.md, marginLeft: spacing.xl },
  errorText: { color: "#D64545", marginBottom: spacing.xs },
  link: { fontWeight: "600", color: "#0B2447" },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
  invitedNote: { fontSize: 13, opacity: 0.75, marginBottom: spacing.md },
});