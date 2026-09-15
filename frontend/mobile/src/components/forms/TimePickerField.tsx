import React, { useMemo, useRef, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Clock, X } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * A time of day, chosen from a list rather than typed.
 *
 * WHY THIS REPLACED A TextInput. Opening and closing time were two
 * free-text boxes with an "08:00" placeholder and no validation
 * anywhere -- frontend, schema or column (opening_time is
 * db.String(5), "free-form per frontend contract"). So "8", "8am",
 * "eight", "0800" and "" were all equally acceptable to everything
 * downstream, and the column is read back into a UI that assumes
 * "HH:mm". Nothing would have failed loudly; the screen would just
 * show whatever was typed, forever.
 *
 * It was also the worse of the two bugs on the screen. A text box at
 * the bottom of a scroll view raises the keyboard over the Save
 * button, so the flow was: type, dismiss keyboard, scroll, save. A
 * sheet has none of that -- and a value that cannot be malformed needs
 * no validation message, which is the cheapest kind of correctness
 * there is.
 *
 * THIRTY-MINUTE STEPS, 04:00 TO 23:30. Shops open on the hour and the
 * half hour; five-minute precision on a spaza's opening time is a
 * number nobody will keep accurate and no code reads. The range starts
 * at 04:00 because early markets are real and ends at 23:30 because
 * "closes at midnight" is 00:00 the next day, which this field cannot
 * express and should not pretend to.
 *
 * CLEARABLE, because both fields are optional and a picker with no way
 * back to "not set" is a trap -- somebody taps it to see what it does
 * and can never undo that.
 *
 * NO NEW DEPENDENCY. @react-native-community/datetimepicker is not
 * installed, and its native dialog returns a full Date for a value
 * that is two integers. This follows the Modal + backdrop + bottom
 * sheet shape already used by ImageActionSheet, SortOptionsSheet and
 * DeclineReasonSheet.
 */

const FIRST_HOUR = 4;
const LAST_HOUR = 23;

function buildOptions(): string[] {
  const out: string[] = [];
  for (let hour = FIRST_HOUR; hour <= LAST_HOUR; hour++) {
    out.push(`${String(hour).padStart(2, "0")}:00`);
    out.push(`${String(hour).padStart(2, "0")}:30`);
  }
  return out;
}

export function TimePickerField({
  label,
  value,
  onChange,
  placeholder = "Not set",
}: {
  label: string;
  /** "HH:mm", or null/undefined when unset. */
  value?: string | null;
  onChange: (value: string | undefined) => void;
  placeholder?: string;
}) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [open, setOpen] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  const options = useMemo(buildOptions, []);
  const selectedIndex = value ? options.indexOf(value) : -1;

  const choose = (time: string) => {
    onChange(time);
    setOpen(false);
  };

  return (
    <View style={styles.field}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>

      <Pressable
        onPress={() => setOpen(true)}
        style={({ pressed }) => [
          styles.control,
          {
            borderColor: theme.colors.outline,
            backgroundColor: pressed ? theme.colors.surfaceVariant : "transparent",
          },
        ]}
        accessibilityRole="button"
        accessibilityLabel={`${label}. ${value ?? placeholder}. Opens a list of times.`}
      >
        <Clock size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
        <Text
          style={[
            styles.value,
            { color: value ? theme.colors.onSurface : theme.colors.onSurfaceVariant },
          ]}
        >
          {value ?? placeholder}
        </Text>
        {value ? (
          // STOPS THE SHEET OPENING. Without stopPropagation the parent
          // Pressable also fires and the clear is immediately followed
          // by a picker nobody asked for.
          <Pressable
            onPress={(event) => {
              event.stopPropagation();
              onChange(undefined);
            }}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`Clear ${label}`}
          >
            <X size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          </Pressable>
        ) : null}
      </Pressable>

      <Modal visible={open} animationType="slide" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <Pressable
            style={[
              styles.sheet,
              {
                backgroundColor: theme.colors.background,
                paddingBottom: spacing.sm + insets.bottom,
              },
            ]}
            onPress={() => {}}
          >
            <View style={[styles.grabber, { backgroundColor: theme.colors.outlineVariant }]} />
            <Text style={[styles.sheetTitle, { color: theme.colors.onSurface }]}>{label}</Text>

            <ScrollView
              ref={scrollRef}
              style={styles.list}
              onLayout={() => {
                // OPENS ON THE CURRENT VALUE, not at 04:00. Forty
                // options is a long way to scroll to confirm the time
                // you already chose.
                if (selectedIndex > 2) {
                  scrollRef.current?.scrollTo({ y: (selectedIndex - 2) * ROW_HEIGHT, animated: false });
                }
              }}
            >
              {options.map((time) => {
                const selected = time === value;
                return (
                  <Pressable
                    key={time}
                    onPress={() => choose(time)}
                    style={({ pressed }) => [
                      styles.row,
                      (pressed || selected) && { backgroundColor: theme.colors.surfaceVariant },
                    ]}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    accessibilityLabel={time}
                  >
                    <Text
                      style={[
                        styles.rowLabel,
                        {
                          color: selected ? theme.colors.primary : theme.colors.onSurface,
                          fontWeight: selected ? "800" : "500",
                        },
                      ]}
                    >
                      {time}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            <Pressable
              onPress={() => {
                onChange(undefined);
                setOpen(false);
              }}
              style={[styles.clear, { borderColor: theme.colors.outlineVariant }]}
              accessibilityRole="button"
              accessibilityLabel={`Clear ${label}`}
            >
              <Text style={[styles.clearLabel, { color: theme.colors.onSurface }]}>Clear</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const ROW_HEIGHT = 48;

const styles = StyleSheet.create({
  field: { gap: spacing.xs, flex: 1 },
  label: { ...typography.bodySmall, fontWeight: "600" },
  control: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: spacing.md,
    minHeight: 48,
  },
  value: { ...typography.body, flex: 1 },
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.45)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  grabber: { alignSelf: "center", width: 36, height: 4, borderRadius: 2, marginBottom: spacing.sm },
  sheetTitle: {
    ...typography.bodySmall,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: spacing.xs,
    marginLeft: spacing.sm,
  },
  // CAPPED, so the sheet never grows past about half the screen on a
  // tall phone and the Clear button stays reachable without scrolling.
  list: { maxHeight: ROW_HEIGHT * 7 },
  row: {
    height: ROW_HEIGHT,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
  },
  rowLabel: { ...typography.body },
  clear: {
    marginTop: spacing.sm,
    minHeight: 48,
    borderRadius: radius.md,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  clearLabel: { ...typography.body, fontWeight: "700" },
});
