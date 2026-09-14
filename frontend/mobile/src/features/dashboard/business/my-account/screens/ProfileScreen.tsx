import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { InlineEditField } from "@/components/ui/InlineEditField";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { AddressPickerField } from "@/features/dashboard/shared/location-picker/components/AddressPickerField";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";
import { useBusinessProfile } from "@/features/dashboard/business/business-profile/hooks/useBusinessProfile";
import { useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks/useBusinessProfileMutations";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useBio } from "../hooks/useBio";
import { useProfileImage } from "../hooks/useProfileImage";
import { useUpdateDisplayName } from "../hooks/useDisplayName";
import { useUpdateContactField } from "../hooks/useContactDetails";
import { ProfileAvatar } from "../components/ProfileAvatar";
import { BIO_MAX_LENGTH } from "../types";

/**
 * Profile — business side.
 *
 * ONE ROW, ONE VALUE, ONE EDIT. Rebuilt to match the supplier's own
 * Profile screen: each field READS as its current value with an
 * explicit "Edit" control and saves itself on confirm
 * (components/ui/InlineEditField), grouped into carded sections under
 * SectionHeadings.
 *
 * WHAT IT REPLACED, AND WHY THAT WAS WORTH DOING. This screen was a
 * stack of always-editable outlined TextInputs behind a single Save
 * button -- the exact design InlineEditField's own docstring records
 * the supplier screen abandoning, because on a phone it is unclear
 * which text is a value you HAVE and which is an input you can change.
 * The two roles disagreeing about that was the real defect; a
 * shopkeeper who is also a supplier met two different ideas of what a
 * profile is.
 *
 * PER-ROW SAVING ALSO REMOVES A REAL FAILURE. The old screen fired up
 * to five mutations from one button and reported one error for all of
 * them, so a rejected phone number looked like the whole save had
 * failed. Now the row that failed says so and the rest are already
 * saved.
 *
 * WHAT IS GENUINELY SAVED, stated plainly because the mix is not
 * obvious from the screen:
 *
 *   BUSINESS NAME   real -- PATCH /business-profile/business-details.
 *   PIN YOUR SHOP   real -- PATCH /business-profile/location, and the
 *                   coordinates are what "Collect near you" needs to
 *                   render at all.
 *   NAME/PHONE/BIO  MOCK, because no account-level endpoint exists to
 *                   save them. The supplier screen has the same gap
 *                   for the same reason. This is not something to fix
 *                   here: the fields belong to the auth/account
 *                   record, and inventing a business-profile write for
 *                   them would break the separation business-profile's
 *                   own types.ts insists on -- "editing account
 *                   settings never silently changes business contact
 *                   info", and the reverse.
 *
 * THE AVATAR IS DELIBERATELY UNTOUCHED. Image upload waits on
 * Cloudinary being set up; this pass changes inputs only.
 */
export default function ProfileScreen() {
  const router = useRouter();
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { bio, save: saveBio } = useBio();
  const { profileImage } = useProfileImage();
  const updateDisplayName = useUpdateDisplayName();
  const updateContactField = useUpdateContactField();
  const { profile } = useBusinessProfile();
  const { saveBusinessDetails, saveLocation } = useBusinessProfileMutations();

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !summary) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Couldn't load your profile. Check your connection and try again."
          onRetry={refetch}
        />
      </ScreenContainer>
    );
  }

  const fullName = [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email;
  const location = profile?.location;

  // THE PICKER SPEAKS DeliveryLocation; a shop's profile stores a
  // flatter shape. Only the pin really matters here -- a shop profile
  // is not a delivery address, and V2's rule is never to require a
  // street address from an informal business.
  const pinnedLocation: DeliveryLocation | null =
    location?.latitude != null && location?.longitude != null
      ? {
          building: "",
          street: location.physicalAddress ?? "",
          suburb: "",
          city: location.cityOrTown ?? "",
          province: "",
          postalCode: "",
          latitude: location.latitude,
          longitude: location.longitude,
        }
      : null;

  const handlePinned = async (picked: DeliveryLocation) => {
    await saveLocation({
      ...(location ?? {}),
      latitude: picked.latitude,
      longitude: picked.longitude,
      // WHAT THEY CONFIRMED IS WHAT GETS SAVED. The first version only
      // filled these when they were EMPTY, reasoning that moving a pin
      // should not rewrite a town somebody typed. That produced a worse
      // bug than the one it avoided: a shop whose profile already said
      // "Elim" pinned a different town, confirmed it, and the card went
      // on reading "Elim" -- so the app appeared to have saved an
      // address they never chose.
      //
      // Confirming an address IS the intent. The fields fall back to
      // what was there only when the geocoder returned nothing for
      // them, which is normal for a rural or informal pin.
      cityOrTown: picked.city?.trim() || location?.cityOrTown,
      physicalAddress:
        [picked.building, picked.street, picked.suburb].filter((part) => part?.trim()).join(", ") ||
        location?.physicalAddress,
    });
  };

  const card = [
    styles.groupCard,
    { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
  ];

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.avatarBlock}>
          <ProfileAvatar
            name={fullName}
            imageUri={profileImage?.status === "approved" ? profileImage.localUri : null}
            onPress={() => router.push("/business/my-account/profile-image" as any)}
            verified={summary.verification === "VERIFIED"}
          />
        </View>

        <View style={styles.body}>
          <SectionHeading title="Your details" />
          <View style={card}>
            <InlineEditField
              label="Business name"
              value={summary.businessName}
              autoCapitalize="words"
              validate={(v) => (v.trim().length === 0 ? "Enter your business name." : null)}
              onSave={(v) => saveBusinessDetails({ businessName: v.trim() }).then(() => {})}
            />
            <InlineEditField
              label="First name"
              value={summary.firstName}
              autoCapitalize="words"
              onSave={(v) =>
                updateDisplayName
                  .mutateAsync({ firstName: v, lastName: summary.lastName ?? "" })
                  .then(() => {})
              }
            />
            <InlineEditField
              label="Last name"
              value={summary.lastName}
              autoCapitalize="words"
              onSave={(v) =>
                updateDisplayName
                  .mutateAsync({ firstName: summary.firstName ?? "", lastName: v })
                  .then(() => {})
              }
            />
            <InlineEditField
              label="Bio"
              value={bio ?? null}
              multiline
              maxLength={BIO_MAX_LENGTH}
              emptyText="A line about your shop"
              onSave={(v) => Promise.resolve(saveBio(v)).then(() => {})}
            />
            <InlineEditField
              label="Login email"
              value={summary.email}
              disabled
              helperText="Your account login email — changed in Account security, not here."
              noDivider
              onSave={async () => {}}
            />
          </View>

          <SectionHeading title="Contact" />
          <View style={card}>
            <InlineEditField
              label="Phone number"
              value={summary.phoneNumber}
              keyboardType="phone-pad"
              emptyText="Add a number"
              noDivider
              onSave={(v) =>
                updateContactField.mutateAsync({ field: "phone", value: v }).then(() => {})
              }
            />
          </View>

          <SectionHeading
            title="Where your shop is"
            hint={[
              "Used to show you suppliers close enough to collect from.",
              "Only the area is ever shown to anyone — never your exact pin.",
            ].join(" ")}
          />
          <View style={[card, styles.pinCard]}>
            <AddressPickerField
              value={pinnedLocation}
              onSave={handlePinned}
              editLabel="Edit your shop's location"
              searchLabel="Search address"
              mapLabel="Drop a pin"
              pickerTitle="Where your shop is"
              pickerConfirmLabel="Confirm shop location"
            />
            {!pinnedLocation && (
              <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
                Without this, “Collect near you” stays hidden — there is no “near”
                to measure from.
              </Text>
            )}
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  avatarBlock: { alignItems: "center", paddingTop: spacing.lg, paddingBottom: spacing.md },
  body: { paddingHorizontal: spacing.md, gap: spacing.md, marginTop: spacing.sm },
  groupCard: {
    borderWidth: 1,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
  },
  // The picker is not a row of text like its neighbours, so it needs
  // its own breathing room inside the same card shape.
  pinCard: { paddingVertical: spacing.md, gap: spacing.sm },
  hint: { ...typography.caption },
});
