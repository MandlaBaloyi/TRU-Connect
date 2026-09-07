import React from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight, Globe, Lock, Users } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { SwitchCard } from "@/components/lists/CardListUI";
import { OptionCardList } from "@/features/dashboard/shared/settings/components/OptionPickerScreen";
import { useSupplierProfileField } from "@/features/dashboard/supplier/my-account/hooks/useSupplierProfileField";
import { TrackRecordPanel } from "@/features/dashboard/supplier/my-account/components/TrackRecordPanel";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/** Mirrors the backend PhotoVisibility enum
 *  (supplier_profile/models/supplier_profile.py). Values are the wire
 *  strings, not display labels — they go straight into the PATCH. */
const PHOTO_VISIBILITY_OPTIONS = [
  {
    value: "everyone",
    label: "Everyone",
    description: "Any business can see your photo, including in search before you connect.",
    icon: (c: string) => <Globe size={20} color={c} strokeWidth={2} />,
  },
  {
    value: "connections",
    label: "Connections only",
    description: "Only businesses you are already connected with.",
    icon: (c: string) => <Users size={20} color={c} strokeWidth={2} />,
  },
  {
    value: "nobody",
    label: "Nobody",
    description: "Your photo is never shown to any business.",
    icon: (c: string) => <Lock size={20} color={c} strokeWidth={2} />,
  },
];

/**
 * Supplier visibility — WHO SEES WHAT, and nothing else.
 *
 * THE RULE THIS SCREEN EXISTS TO ENFORCE: the profile holds the
 * values, Settings holds who can see them. A supplier used to set both
 * in the same place, which meant the profile was half input form and
 * half privacy console and read as neither. Nothing here is editable —
 * where a value appears below it is read-only, with a link back to the
 * profile. Every control is an on/off (or a who).
 *
 * EACH SWITCH SITS NEXT TO WHAT IT CONTROLS. A switch labelled "share
 * contact details" with the details themselves three screens away is a
 * decision made blind; showing the actual WhatsApp number under the
 * switch is what makes "share" concrete. Same reasoning as
 * LastActiveRow on the Community activity screen, and as the public
 * half of TrackRecordPanel below.
 *
 * NOT EVERYTHING VISIBLE GETS A SWITCH — see the closing note in the
 * render for why delivery terms, minimum order and collection address
 * deliberately have none.
 */
export default function SupplierVisibilityScreen() {
  const theme = useTheme();
  const { profile, saveField, isLoading, refetch } = useSupplierProfileField();

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (!profile) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your visibility settings. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return <VisibilityForm profile={profile} saveField={saveField} />;
}

function VisibilityForm({
  profile,
  saveField,
}: {
  profile: NonNullable<ReturnType<typeof useSupplierProfileField>["profile"]>;
  saveField: ReturnType<typeof useSupplierProfileField>["saveField"];
}) {
  const theme = useTheme();
  const router = useRouter();

  const hasPhoto = Boolean(profile.businessImageUrl);

  const contactRows = [
    { label: "WhatsApp", value: profile.whatsappNumber },
    { label: "Business email", value: profile.contactEmail },
    { label: "TikTok", value: profile.tiktokHandle },
  ];
  const hasAnyContact = contactRows.some((row) => Boolean(row.value));

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* ---- PHOTO ----
            Three states, not a switch: "everyone" and "connections
            only" are both real, sensible answers and a boolean cannot
            hold them both. The default is CONNECTIONS, chosen at
            architecture review precisely because appearing in bare
            search results before any relationship exists is a wider
            exposure than being seen by someone you already deal with —
            so going wider must be an explicit choice, never a silent
            default. */}
        <View style={styles.body}>
          <SectionHeading
            title="Who can see your photo"
            hint={[
              "Applies to your profile photo and cover banner wherever they appear — search results, your profile, and your connections list.",
              "Everyone means a business can see your photo before connecting, which helps them recognise you when searching.",
              "This controls WHO sees the photo. Changing or removing the photo itself is done on your Profile.",
            ]}
          />

          <OptionCardList
            options={PHOTO_VISIBILITY_OPTIONS}
            selected={profile.photoVisibility}
            onSelect={(photoVisibility) => saveField({ photoVisibility })}
          />

          {/* An honest correction to a setting that would otherwise
              look effective. Choosing "Everyone" with no photo
              uploaded changes nothing a business can see, and a
              supplier should be told that here rather than wondering
              why nothing happened. */}
          {!hasPhoto && (
            <NoteRow
              text="You haven't added a profile photo yet, so nothing is shown to anyone regardless of the choice above."
              actionLabel="Add one on your Profile"
              onPress={() => router.push("/supplier/my-account/profile" as any)}
            />
          )}

          {/* ---- CONTACT DETAILS ---- */}
          <SectionHeading
            title="Business contact details"
            hint={[
              "Shown only to businesses you're connected with, on the products they view from you.",
              "Separate from your login email — this never changes how you sign in.",
              "Turn it off and none of it is shown to anyone, even connected businesses. The details themselves are kept, not deleted.",
            ]}
          />

          <SwitchCard
            label="Share contact details"
            description="Connected businesses can see the details below."
            value={profile.shareContactDetails}
            onValueChange={(shareContactDetails) => saveField({ shareContactDetails })}
          />

          {/* READ-ONLY ON PURPOSE. These are the values the switch
              governs, shown so the choice is concrete, but this screen
              never edits them — that is what the Profile is for. */}
          <View style={[styles.groupCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            {hasAnyContact ? (
              contactRows.map((row) => (
                <View key={row.label} style={styles.readRow}>
                  <Text style={[styles.readLabel, { color: theme.colors.onSurfaceVariant }]}>{row.label}</Text>
                  <Text
                    style={[
                      styles.readValue,
                      { color: row.value ? theme.colors.onSurface : theme.colors.onSurfaceVariant },
                    ]}
                    numberOfLines={1}
                  >
                    {row.value || "Not added"}
                  </Text>
                </View>
              ))
            ) : (
              <View style={styles.readRow}>
                <Text style={[styles.readValue, { color: theme.colors.onSurfaceVariant }]}>
                  You haven't added any contact details yet.
                </Text>
              </View>
            )}
          </View>

          <LinkRow label="Edit contact details on your Profile" onPress={() => router.push("/supplier/my-account/profile" as any)} />

          {/* ---- TRACK RECORD ----
              The panel shows MORE than the switch controls: the public
              counts businesses would see, plus the private figures
              (acceptance rate, reply time, cancellations) that are
              never shown to anyone. Both are here because seeing the
              real numbers is what makes "show my track record" a
              decision rather than a guess.

              STILL THE SEED OF AN ANALYTICS SCREEN. It sat on the
              profile before this, for the same reason it sits here
              now: no analytics section exists yet. When one does, this
              panel moves there and this screen keeps only the
              switch. */}
          <SectionHeading
            title="Your track record"
            hint={[
              "Your real trading figures, built from actual orders — nothing here is self-reported, and nothing can be typed in.",
              "Businesses see three figures and nothing else. Everything else on this screen and in your own panel stays private — your acceptance rate, reply time, cancellations, total sales, units sold and repeat buyers are there to help you improve, not to be judged on.",
              "The switch controls only what businesses see. You always see your own panel.",
            ]}
          />

          <SwitchCard
            label="Show my track record to businesses"
            description="When off, the whole track-record section disappears from your profile."
            value={profile.showTrackRecord}
            onValueChange={(showTrackRecord) => saveField({ showTrackRecord })}
          />

          {/* THE EXACT PUBLIC SET, NAMED. A supplier deciding whether
              to switch this on is entitled to know precisely what it
              exposes, and "your track record" is not an answer. These
              three are the complete list -- the backend payload behind
              them carries nothing else (see trust_stats_for_supplier's
              own docstring, which points back here). If a fourth
              figure is ever added, this list is wrong the same day. */}
          <View style={[styles.publicSet, { borderColor: theme.colors.outlineVariant }]}>
            <Text style={[styles.publicSetTitle, { color: theme.colors.onSurface }]}>
              {profile.showTrackRecord ? "What businesses see" : "What businesses would see"}
            </Text>
            {[
              { label: "Businesses connected", note: "How many businesses you are connected with." },
              { label: "Orders accepted", note: "Orders you took on, all time." },
              { label: "Orders fulfilled", note: "Coming soon — nothing records delivery yet, so it shows no number." },
            ].map((row) => (
              <View key={row.label} style={styles.publicSetRow}>
                <View style={[styles.bullet, { backgroundColor: theme.colors.primary }]} />
                <View style={styles.publicSetText}>
                  <Text style={[styles.publicSetLabel, { color: theme.colors.onSurface }]}>{row.label}</Text>
                  <Text style={[styles.publicSetNote, { color: theme.colors.onSurfaceVariant }]}>{row.note}</Text>
                </View>
              </View>
            ))}
          </View>

          <SectionHeading title="Private to you" />
          <TrackRecordPanel performance={profile.performance} />

          {/* ---- WHAT HAS NO SWITCH, AND WHY ----
              Delivery terms and minimum order are what a business
              checks BEFORE deciding to connect, and the minimum is
              ENFORCED at checkout: hiding it would let a business fill
              a cart and then be blocked by a rule it was never shown.
              That is a broken flow, not a private one. The collection
              address is already restricted to connected businesses by
              the backend, and leaving it unset already means it is not
              shown — a switch would be a second way of saying the same
              thing. So this is a signpost, not a control. */}
          <View style={[styles.alwaysShown, { borderColor: theme.colors.outlineVariant }]}>
            <Text style={[styles.alwaysShownTitle, { color: theme.colors.onSurface }]}>Always shown</Text>
            <Text style={[styles.alwaysShownBody, { color: theme.colors.onSurfaceVariant }]}>
              Your delivery terms and minimum order are shown to every business — they're what a business checks before
              ordering, and the minimum is applied at checkout either way. Your collection address is shown only to
              businesses you're connected with. Leave any of them unset and nothing is shown for it.
            </Text>
            <LinkRow label="Set them on your Profile" onPress={() => router.push("/supplier/my-account/profile" as any)} />
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

function LinkRow({ label, onPress }: { label: string; onPress: () => void }) {
  const theme = useTheme();
  return (
    <Pressable onPress={onPress} style={styles.linkRow} accessibilityRole="button" accessibilityLabel={label}>
      <Text style={[styles.linkText, { color: theme.colors.primary }]}>{label}</Text>
      <ChevronRight size={16} color={theme.colors.primary} strokeWidth={2.4} />
    </Pressable>
  );
}

function NoteRow({ text, actionLabel, onPress }: { text: string; actionLabel: string; onPress: () => void }) {
  const theme = useTheme();
  return (
    <View style={styles.note}>
      <Text style={[styles.noteText, { color: theme.colors.onSurfaceVariant }]}>{text}</Text>
      <LinkRow label={actionLabel} onPress={onPress} />
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  body: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, gap: spacing.md },
  groupCard: {
    borderWidth: 1,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  readRow: { paddingVertical: spacing.sm, gap: 2 },
  readLabel: { ...typography.caption, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  readValue: { ...typography.body },
  linkRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40 },
  linkText: { ...typography.bodySmall, fontWeight: "700" },
  note: { gap: 2 },
  noteText: { ...typography.bodySmall, lineHeight: 18 },
  alwaysShown: {
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.md,
    gap: spacing.xs,
    marginTop: spacing.sm,
  },
  alwaysShownTitle: { ...typography.body, fontWeight: "700" },
  alwaysShownBody: { ...typography.bodySmall, lineHeight: 19 },

  publicSet: { borderWidth: 1, borderRadius: radius.lg, padding: spacing.md, gap: spacing.sm },
  publicSetTitle: { ...typography.body, fontWeight: "700" },
  publicSetRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm },
  bullet: { width: 6, height: 6, borderRadius: 3, marginTop: 7 },
  publicSetText: { flex: 1, gap: 1 },
  publicSetLabel: { ...typography.bodySmall, fontWeight: "700" },
  publicSetNote: { ...typography.bodySmall, fontSize: 12, lineHeight: 17 },
});
