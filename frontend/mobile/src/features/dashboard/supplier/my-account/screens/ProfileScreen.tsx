import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { SwitchCard } from "@/components/lists/CardListUI";
import { ImageActionSheet } from "@/components/ui/ImageActionSheet";
import { FullScreenImageViewer } from "@/components/ui/FullScreenImageViewer";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useUpdateDisplayName } from "../hooks/useDisplayName";
import { useSupplierProfile } from "../hooks/useSupplierProfile";
import { useProfileImageUpload } from "../hooks/useProfileImageUpload";
import type { SupplierProfileData } from "../services/accountService";
import type { AccountProfileSummary } from "../types";
import type { ProfileImageSlot } from "../services/profileImageUpload";
import { ProfileHeader } from "../components/ProfileHeader";
import { InlineEditField } from "../components/InlineEditField";
import { CollectionAddressField } from "../components/CollectionAddressField";
import { InfoHint } from "@/components/ui/InfoHint";
import { formatCents } from "../../products/services/productMapper";
import { BIO_MAX_LENGTH } from "../types";

/**
 * Profile — supplier side.
 *
 * HEADER (components/ProfileHeader.tsx, shared with the My Account
 * landing screen): a full-bleed cover banner with the circular avatar
 * overlapping its lower edge, business name then personal name below.
 * Here it's `editable` -- tapping either image opens an action sheet
 * (View / Take photo / Choose from gallery / Remove / Cancel); "View"
 * opens a pinch-to-zoom fullscreen viewer. Both images upload straight
 * to Cloudinary, scoped to this supplier's own folder; what's shown is
 * always the stored url on SupplierProfile, never local device state.
 *
 * FIELDS are grouped into two carded sections -- "Your details" and
 * "Business contact details" -- each row reading as its CURRENT VALUE
 * with an explicit "Edit" control (components/InlineEditField.tsx),
 * saving itself on confirm. Business name, bio and the three contact
 * channels go through the real PATCH /supplier-discovery/my-profile
 * (category / location / photoVisibility / visibleImageSource passed
 * through UNCHANGED). First/last name use updateDisplayName. The login
 * email is READ-ONLY here -- it's the account credential, changed in
 * Account security (not built for the supplier role yet). Phone number
 * was removed: a customer-facing number belongs in Business contact
 * details, not next to the login email.
 */
export default function ProfileScreen() {
  const theme = useTheme();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { profile, isLoading: isProfileLoading } = useSupplierProfile();

  if (isLoading || isProfileLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !summary || !profile) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your profile. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return <ProfileForm summary={summary} profile={profile} />;
}

function ProfileForm({ summary, profile }: { summary: AccountProfileSummary; profile: SupplierProfileData }) {
  const theme = useTheme();
  const { save: saveProfile } = useSupplierProfile();
  const updateDisplayName = useUpdateDisplayName();
  const { busySlot, error: imageError, pickAndUpload, remove: removeImage } = useProfileImageUpload();

  const [sheetSlot, setSheetSlot] = useState<ProfileImageSlot | null>(null);
  const [viewerUri, setViewerUri] = useState<string | null>(null);

  const fullName = [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email;
  const displayName = profile.businessName?.trim() || fullName;

  /** One field changed -- PATCH the whole SupplierProfile with every
   *  other field passed through untouched. */
  const saveProfileField = (patch: Partial<SupplierProfileData>) =>
    saveProfile({
      businessName: profile.businessName,
      category: profile.category,
      location: profile.location,
      description: profile.description,
      photoVisibility: profile.photoVisibility,
      visibleImageSource: profile.visibleImageSource,
      businessImageUrl: profile.businessImageUrl,
      coverImageUrl: profile.coverImageUrl,
      whatsappNumber: profile.whatsappNumber,
      contactEmail: profile.contactEmail,
      tiktokHandle: profile.tiktokHandle,
      shareContactDetails: profile.shareContactDetails,
      offersDelivery: profile.offersDelivery,
      minimumOrderCents: profile.minimumOrderCents,
      collectionBuilding: profile.collectionBuilding,
      collectionStreet: profile.collectionStreet,
      collectionSuburb: profile.collectionSuburb,
      collectionCity: profile.collectionCity,
      collectionProvince: profile.collectionProvince,
      collectionPostalCode: profile.collectionPostalCode,
      collectionLatitude: profile.collectionLatitude,
      collectionLongitude: profile.collectionLongitude,
      ...patch,
    });

  const sheetImageUri = sheetSlot === "cover" ? profile.coverImageUrl : profile.businessImageUrl;

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ProfileHeader
          editable
          displayName={displayName}
          secondaryName={fullName}
          coverUri={profile.coverImageUrl}
          avatarUri={profile.businessImageUrl}
          verified={summary.verification === "VERIFIED"}
          busySlot={busySlot}
          onCoverPress={() => setSheetSlot("cover")}
          onAvatarPress={() => setSheetSlot("profile")}
        />
        {imageError && <Text style={[styles.error, { color: theme.colors.error }]}>{imageError}</Text>}

        {/* --- Editable fields --- */}
        <View style={styles.body}>
          <SectionHeading title="Your details" />
          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <InlineEditField
              label="Business name"
              value={profile.businessName}
              autoCapitalize="words"
              validate={(v) => (v.length === 0 ? "Enter your business name." : null)}
              onSave={(v) => saveProfileField({ businessName: v }).then(() => {})}
            />
            <InlineEditField
              label="First name"
              value={summary.firstName}
              autoCapitalize="words"
              onSave={(v) => updateDisplayName.mutateAsync({ firstName: v, lastName: summary.lastName ?? "" }).then(() => {})}
            />
            <InlineEditField
              label="Last name"
              value={summary.lastName}
              autoCapitalize="words"
              onSave={(v) => updateDisplayName.mutateAsync({ firstName: summary.firstName ?? "", lastName: v }).then(() => {})}
            />
            <InlineEditField
              label="Bio"
              value={profile.description}
              multiline
              maxLength={BIO_MAX_LENGTH}
              emptyText="Tell connected businesses what you sell"
              onSave={(v) => saveProfileField({ description: v || null }).then(() => {})}
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

          <SectionHeading
            title="Business contact details"
            hint={[
              "Shown only to businesses you're connected with, on the products they view from you.",
              "Separate from your login email above — changing these never changes how you sign in.",
            ]}
          />

          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <InlineEditField
              label="WhatsApp number"
              value={profile.whatsappNumber}
              keyboardType="phone-pad"
              placeholder="e.g. 27821234567"
              helperText="Include the country code, no + or spaces."
              emptyText="Not shared"
              onSave={(v) => saveProfileField({ whatsappNumber: v || null }).then(() => {})}
            />
            <InlineEditField
              label="Business contact email"
              value={profile.contactEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              emptyText="Not shared"
              onSave={(v) => saveProfileField({ contactEmail: v || null }).then(() => {})}
            />
            <InlineEditField
              label="TikTok handle"
              value={profile.tiktokHandle}
              autoCapitalize="none"
              placeholder="e.g. myshop"
              emptyText="Not shared"
              noDivider
              onSave={(v) => saveProfileField({ tiktokHandle: v || null }).then(() => {})}
            />
          </View>

          <SwitchCard
            label="Share these with connected businesses"
            description="When off, none of the above is shown to anyone — even businesses you're connected with."
            value={profile.shareContactDetails}
            onValueChange={(val) => saveProfileField({ shareContactDetails: val })}
          />

          {/* --- Fulfilment terms ---
              Unlike the contact details above, these are shown to ANY
              business viewing your profile, connected or not: they're
              what a business needs while deciding whether to connect at
              all, so hiding them until after connection would mean they
              find out too late. The ⓘ on the heading says so, rather
              than a permanent paragraph a supplier reads once. */}
          <SectionHeading
            title="How you fulfil orders"
            hint={[
              "Shown on your profile to ANY business, connected or not — it's what they check before deciding to order from you.",
              "Delivery: pick one and businesses see it. Leave it unset and they see no delivery terms at all.",
              "Minimum order: leave it blank for no minimum. Businesses can't check out below the amount you set.",
            ]}
          />

          {/* A CHOICE, NOT A SWITCH. offersDelivery is tri-state and a
              switch can only express two -- an untouched switch reads
              as "off", which would silently tell every business
              "collection only" on behalf of a supplier who never said
              it. Until one of these is picked, businesses simply see
              no delivery terms at all. */}
          <View style={styles.deliveryChoiceRow}>
            {[
              { value: true, label: "I deliver" },
              { value: false, label: "Collection only" },
            ].map((option) => {
              const selected = profile.offersDelivery === option.value;
              return (
                <Pressable
                  key={option.label}
                  onPress={() => saveProfileField({ offersDelivery: option.value })}
                  style={[
                    styles.deliveryChoice,
                    { borderColor: selected ? theme.colors.primary : theme.colors.outline },
                    selected && { backgroundColor: theme.colors.primaryContainer },
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  accessibilityLabel={option.label}
                >
                  <Text
                    style={[
                      styles.deliveryChoiceLabel,
                      { color: selected ? theme.colors.primary : theme.colors.onSurface },
                    ]}
                  >
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          {profile.offersDelivery === null && (
            <Text style={[styles.sectionHint, { color: theme.colors.onSurfaceVariant }]}>
              Not set yet — businesses won't see any delivery terms until you choose.
            </Text>
          )}

          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <InlineEditField
              label="Minimum order"
              // Rands in the field, cents on the wire -- every money
              // value in this codebase is stored in cents, and a
              // supplier should never have to think in them.
              // Edits as a plain number, READS as currency -- "500"
              // alone left it ambiguous whether it meant rands or cents.
              value={profile.minimumOrderCents !== null ? String(profile.minimumOrderCents / 100) : null}
              displayValue={profile.minimumOrderCents !== null ? formatCents(profile.minimumOrderCents) : null}
              keyboardType="numeric"
              placeholder="e.g. 500"
              emptyText="No minimum"
              noDivider
              validate={(v) => {
                if (v.trim().length === 0) return null; // blank = no minimum
                const rands = Number(v);
                if (!Number.isFinite(rands) || rands <= 0) return "Enter an amount more than R0, or leave blank.";
                return null;
              }}
              onSave={(v) =>
                saveProfileField({
                  minimumOrderCents: v.trim().length === 0 ? null : Math.round(Number(v) * 100),
                }).then(() => {})
              }
            />
          </View>

          {/* WHERE BUSINESSES COLLECT FROM. Same Mapbox search +
              map-confirm flow the business delivery address uses --
              see CollectionAddressField's own docstring on why it
              reuses those components rather than inventing a second
              address UI. Shown only to CONNECTED businesses (backend
              gate) -- the heading's ⓘ says so. */}
          <SectionHeading
            title="Collection address"
            hint={[
              "Where businesses come to collect their orders.",
              "Only shown to businesses you're connected with — unlike your delivery terms, this is a real street address, so it stays behind a connection.",
            ]}
          />

          <CollectionAddressField
            value={
              profile.collectionStreet || profile.collectionSuburb
                ? {
                    building: profile.collectionBuilding ?? "",
                    street: profile.collectionStreet ?? "",
                    suburb: profile.collectionSuburb ?? "",
                    city: profile.collectionCity ?? "",
                    province: profile.collectionProvince ?? "",
                    postalCode: profile.collectionPostalCode ?? "",
                    latitude: profile.collectionLatitude ?? 0,
                    longitude: profile.collectionLongitude ?? 0,
                  }
                : null
            }
            onSave={(location) =>
              saveProfileField({
                collectionBuilding: location.building || null,
                collectionStreet: location.street || null,
                collectionSuburb: location.suburb || null,
                collectionCity: location.city || null,
                collectionProvince: location.province || null,
                collectionPostalCode: location.postalCode || null,
                collectionLatitude: location.latitude,
                collectionLongitude: location.longitude,
              }).then(() => {})
            }
          />

        </View>
      </ScrollView>

      <ImageActionSheet
        visible={sheetSlot !== null}
        title={sheetSlot === "cover" ? "Cover photo" : "Profile photo"}
        hasImage={Boolean(sheetImageUri)}
        onView={() => sheetImageUri && setViewerUri(sheetImageUri)}
        onTakePhoto={() => sheetSlot && pickAndUpload(sheetSlot, "CAMERA")}
        onChooseFromGallery={() => sheetSlot && pickAndUpload(sheetSlot, "LIBRARY")}
        onRemove={() => sheetSlot && removeImage(sheetSlot)}
        onClose={() => setSheetSlot(null)}
      />

      <FullScreenImageViewer visible={viewerUri !== null} uri={viewerUri} onClose={() => setViewerUri(null)} />
    </ScreenContainer>
  );
}

/**
 * A section heading, with its explanation behind an ⓘ rather than in a
 * permanent grey paragraph underneath.
 *
 * WHY: this screen had grown four such paragraphs, and together they
 * meant a supplier scrolled through more explanation than actual
 * profile. Each sentence was individually justified; the total wasn't.
 * The heading names the section, the ⓘ explains it, and a supplier who
 * already knows never pays for it.
 */
function SectionHeading({ title, hint }: { title: string; hint?: string | string[] }) {
  const theme = useTheme();
  return (
    <View style={styles.sectionHeadingRow}>
      <Text style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}>{title}</Text>
      {hint && <InfoHint title={title} body={hint} size={15} />}
    </View>
  );
}

const styles = StyleSheet.create({
  sectionHeadingRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.sm },
  deliveryChoiceRow: { flexDirection: "row", gap: spacing.sm },
  deliveryChoice: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  deliveryChoiceLabel: { ...typography.bodySmall, fontWeight: "700" },
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  error: { ...typography.bodySmall, marginTop: spacing.sm, paddingHorizontal: spacing.md, textAlign: "center" },

  body: { paddingHorizontal: spacing.md, gap: spacing.md, marginTop: spacing.sm },
  groupCard: {
    borderWidth: 1,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  sectionTitle: { ...typography.caption, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  sectionHint: { ...typography.bodySmall, lineHeight: 18 },
});
