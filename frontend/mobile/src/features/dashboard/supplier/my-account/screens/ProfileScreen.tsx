import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { showsAsVerified } from "@/constants/config";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ImageActionSheet } from "@/components/ui/ImageActionSheet";
import { FullScreenImageViewer } from "@/components/ui/FullScreenImageViewer";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useAccountProfile } from "../hooks/useAccountProfile";
import { useUpdateDisplayName } from "../hooks/useDisplayName";
import { useSupplierProfile } from "../hooks/useSupplierProfile";
import { useSupplierProfileField } from "../hooks/useSupplierProfileField";
import { useProfileImageUpload } from "../hooks/useProfileImageUpload";
import type { SupplierProfileData } from "../services/accountService";
import type { AccountProfileSummary } from "../types";
import type { ProfileImageSlot } from "../services/profileImageUpload";
import { ProfileHeader } from "../components/ProfileHeader";
import { ProfileOverflowMenu } from "../components/ProfileOverflowMenu";
import { InlineEditField } from "../components/InlineEditField";
import { CollectionAddressField } from "../components/CollectionAddressField";
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
 * FIELDS are grouped into carded sections -- "Your details",
 * "Business contact details", fulfilment terms, collection address --
 * each row reading as its CURRENT VALUE with an explicit "Edit"
 * control (components/InlineEditField.tsx), saving itself on confirm.
 * Everything goes through the real PATCH
 * /supplier-discovery/my-profile via useSupplierProfileField, which
 * owns the pass-through of every field this screen isn't changing.
 * First/last name use updateDisplayName instead. The login email is
 * READ-ONLY here -- it's the account credential, changed in Account
 * security (not built for the supplier role yet). Phone number was
 * removed: a customer-facing number belongs in Business contact
 * details, not next to the login email.
 *
 * THIS SCREEN HOLDS VALUES, NOT VISIBILITY. Three switches used to
 * live here -- share contact details, show last active, show track
 * record -- along with the track-record panel and the last-active
 * preview. They are gone, to Settings (supplier/settings/screens/
 * SupplierVisibilityScreen.tsx and CommunityActivityScreen.tsx).
 *
 * The reason is that they were never profile information. A profile is
 * what you tell businesses; a visibility switch is who gets to hear
 * it. Mixing them made this screen half input form and half privacy
 * console, and it read as neither -- it was long enough that the
 * actual editable fields were buried under explanation belonging to
 * settings. What stays behind is a short signpost at the bottom, so a
 * supplier who looks for a switch here still finds their way.
 *
 * The one exception is the CONTACT SHARING STATE, echoed as a single
 * read-only line under the contact card. Not a control -- editing a
 * WhatsApp number while unable to tell whether it is being shared with
 * anyone is the one place where splitting value from visibility would
 * genuinely mislead.
 */
export default function ProfileScreen() {
  const theme = useTheme();
  const navigation = useNavigation();

  const { summary, isLoading, isError, refetch } = useAccountProfile();
  const { profile, isLoading: isProfileLoading } = useSupplierProfile();

  /**
   * THE HEADER FLASH FIX, reported directly: opening this screen showed
   * "Profile" for a beat before swapping to the business name and
   * avatar. Same class of bug and same fix as SupplierCatalogScreen's
   * own "Stock Catalogue" flash (see its comment for the full
   * reasoning) -- the title could only become real once a request
   * resolved.
   *
   * TWO PARTS, and this is the second of them.
   *
   * (1) The supplier's own profile is now PREFETCHED when the
   *     dashboard mounts (supplier/(tabs)/_layout.tsx), so by the time
   *     any of the four screens that read it are opened, the React
   *     Query cache already holds it.
   *
   * (2) This effect lives on the OUTER component, above the loading
   *     and error early-returns, rather than inside ProfileForm.
   *     That is the part that actually removes the flash: ProfileForm
   *     only mounts AFTER loading finishes, so a header set from
   *     inside it could never be set on the first frame no matter how
   *     warm the cache was. Up here, a cached profile is read
   *     synchronously on the very first render and useLayoutEffect
   *     commits the header before paint.
   *
   * Falls back to the _layout.tsx "Profile" string only while the name
   * is genuinely unknown -- exactly the catalogue's own
   * `...(name ? {headerTitle} : {})` shape. A wrong-but-styled header
   * would be worse than a plain one.
   */
  const headerName = profile?.businessName?.trim() || null;

  useLayoutEffect(() => {
    navigation.setOptions({
      ...(headerName
        ? {
            headerTitle: () => (
              <EntityHeaderTitle
                name={headerName}
                subtitle="Your profile"
                photoUrl={profile?.businessImageUrl}
                verified={showsAsVerified(summary?.verification)}
              />
            ),
          }
        : {}),
      headerRight: () => <ProfileOverflowMenu />,
    });
  }, [navigation, headerName, profile?.businessImageUrl, summary?.verification]);

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
  const router = useRouter();
  /** One field changed -- PATCH the whole SupplierProfile with every
   *  other field passed through untouched. That pass-through list is
   *  the hook's job, not this screen's: Settings writes the same row
   *  now, and two hand-maintained copies of "all the fields" would
   *  eventually drop one silently. */
  const { saveField: saveProfileField } = useSupplierProfileField();
  const updateDisplayName = useUpdateDisplayName();
  const { busySlot, error: imageError, pickAndUpload, remove: removeImage } = useProfileImageUpload();

  const [sheetSlot, setSheetSlot] = useState<ProfileImageSlot | null>(null);
  const [viewerUri, setViewerUri] = useState<string | null>(null);

  const fullName = [summary.firstName, summary.lastName].filter(Boolean).join(" ") || summary.email;
  const displayName = profile.businessName?.trim() || fullName;

  /* THE TOP BAR CARRIES THE BUSINESS, not the word "Profile" -- the
     avatar, name and tick a BUSINESS sees when it opens this
     supplier's brand profile, rendered by the identical component so a
     supplier is looking at exactly what their customers look at.
     "Profile" as a title told them nothing they did not already know.

     WIRED IN THE OUTER ProfileScreen, not here, and that placement is
     the whole flash fix -- see the long comment there. This component
     only mounts once loading is done, so a header set from here can
     never make the first frame. */

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
          verified={showsAsVerified(summary.verification)}
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
              "Whether they're shared at all is a Settings choice, under Supplier visibility.",
            ]}
          />

          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <InlineEditField
              label="WhatsApp number"
              value={profile.whatsappNumber}
              keyboardType="phone-pad"
              placeholder="e.g. 27821234567"
              helperText="Include the country code, no + or spaces."
              emptyText="Not added"
              onSave={(v) => saveProfileField({ whatsappNumber: v || null }).then(() => {})}
            />
            <InlineEditField
              label="Business contact email"
              value={profile.contactEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              emptyText="Not added"
              onSave={(v) => saveProfileField({ contactEmail: v || null }).then(() => {})}
            />
            <InlineEditField
              label="TikTok handle"
              value={profile.tiktokHandle}
              autoCapitalize="none"
              placeholder="e.g. myshop"
              emptyText="Not added"
              noDivider
              onSave={(v) => saveProfileField({ tiktokHandle: v || null }).then(() => {})}
            />
          </View>

          {/* STATE, NOT A CONTROL. The switch itself lives in Settings
              (Supplier visibility) with the rest of the visibility
              choices. This line stays because editing a contact number
              while unable to tell whether anyone is being shown it is
              the one case where the split would genuinely mislead --
              so the answer travels with the fields, and the switch
              does not. */}
          <SharingStatusRow
            isShared={profile.shareContactDetails}
            onPress={() => router.push("/supplier/settings/supplier-visibility" as any)}
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


          {/* ---- WHERE THE SWITCHES WENT ----
              A signpost, not a section. Activity status and track
              record used to render here in full -- two headings, two
              switches, a stats panel and a preview row. All of it was
              answering "who can see this", which is a Settings
              question, so all of it moved. What a supplier loses by
              that move is knowing where to look, and this is the two
              lines that give it back. */}
          <SectionHeading
            title="Visibility"
            hint={[
              "Your profile holds what you tell businesses. Settings holds who gets to see it.",
              "Photo visibility, contact sharing and your track record are under Supplier visibility. Your activity status is under Community activity.",
            ]}
          />

          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            <SettingsLinkRow
              label="Supplier visibility"
              description="Who sees your photo, contact details and track record"
              onPress={() => router.push("/supplier/settings/supplier-visibility" as any)}
            />
            <SettingsLinkRow
              label="Community activity"
              description="Whether businesses see when you were last active"
              noDivider
              onPress={() => router.push("/supplier/settings/community-activity" as any)}
            />
          </View>
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
 * Whether the contact details above are reaching anyone, stated in the
 * words that matter to a supplier, with a way to change it.
 *
 * It reads as a status line rather than a switch on purpose -- the
 * switch is in Settings, and having a second one here would give two
 * controls for one value on two screens a supplier moves between.
 */
function SharingStatusRow({ isShared, onPress }: { isShared: boolean; onPress: () => void }) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={styles.sharingRow}
      accessibilityRole="button"
      accessibilityLabel={
        isShared ? "Contact details are shared. Change in Supplier visibility." : "Contact details are not shared. Change in Supplier visibility."
      }
    >
      <View style={[styles.sharingDot, { backgroundColor: isShared ? theme.colors.secondary : theme.colors.outline }]} />
      <Text style={[styles.sharingText, { color: theme.colors.onSurfaceVariant }]}>
        {isShared
          ? "Shared with connected businesses"
          : "Not shared — nobody sees these"}
      </Text>
      <Text style={[styles.sharingAction, { color: theme.colors.primary }]}>Change</Text>
      <ChevronRight size={14} color={theme.colors.primary} strokeWidth={2.4} />
    </Pressable>
  );
}

/** A row inside a group card that navigates instead of editing. */
function SettingsLinkRow({
  label,
  description,
  noDivider,
  onPress,
}: {
  label: string;
  description: string;
  noDivider?: boolean;
  onPress: () => void;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.linkRow,
        !noDivider && { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: theme.colors.outlineVariant },
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      <View style={styles.linkRowText}>
        <Text style={[styles.linkRowLabel, { color: theme.colors.onSurface }]}>{label}</Text>
        <Text style={[styles.linkRowDescription, { color: theme.colors.onSurfaceVariant }]}>{description}</Text>
      </View>
      <ChevronRight size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
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
  sectionHint: { ...typography.bodySmall, lineHeight: 18 },

  sharingRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40 },
  sharingDot: { width: 8, height: 8, borderRadius: 4 },
  sharingText: { ...typography.bodySmall, flex: 1 },
  sharingAction: { ...typography.bodySmall, fontWeight: "700" },

  linkRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.md },
  linkRowText: { flex: 1, gap: 2 },
  linkRowLabel: { ...typography.body, fontWeight: "600" },
  linkRowDescription: { ...typography.bodySmall },
});
