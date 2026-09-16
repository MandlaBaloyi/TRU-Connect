import React, { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Check, ChevronDown } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export interface SelectOption {
  value: string;
  label: string;
}

/**
 * A field that opens a list from the bottom, for choosing one thing or
 * several.
 *
 * WHY THIS REPLACED A WALL OF CHIPS. Seventeen product categories
 * rendered as wrapped chips filled most of a phone screen before the
 * reader had answered anything, pushed the second question and the
 * Continue button below the fold, and gave no sense of how much was
 * left. Mandla's words for it: "this confusing one".
 *
 * Chips are right for a SHORT, closed set you want visible at a glance
 * -- "who do you mainly sell to?" is five options and stays chips.
 * They stop working somewhere around eight, and seventeen is well past
 * it. A field plus a sheet keeps the FORM readable: every question is
 * one line, so the shape of what is being asked survives no matter how
 * long the answer list is.
 *
 * THE FIELD SHOWS THE ANSWER, NOT A PROMPT. Once something is chosen
 * the row reads "Food & Grocery, Beverages +2" rather than "Select
 * categories" -- so a person scanning back up the form sees what they
 * said, which is the entire advantage a chip wall had.
 *
 * MULTI-SELECT SHEETS DO NOT CLOSE ON EACH TAP. Picking four
 * categories should be four taps and one dismissal, not four round
 * trips. Single-select closes immediately, because there is nothing
 * further to say.
 *
 * SAME Modal + backdrop + bottom-sheet SHAPE as ImageActionSheet,
 * TimePickerField and SortOptionsSheet, so no new dependency and no
 * new interaction to learn.
 */
export function SelectField({
  label,
  options,
  value,
  onChange,
  multiple = false,
  placeholder = "Tap to choose",
  sheetTitle,
}: {
  label: string;
  options: SelectOption[];
  /** Always an array, even for single select -- one shape for the
   *  caller, so switching a question between one answer and several is
   *  a prop rather than a rewrite. */
  value: string[];
  onChange: (value: string[]) => void;
  multiple?: boolean;
  placeholder?: string;
  sheetTitle?: string;
}) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [open, setOpen] = useState(false);

  const labelFor = useMemo(() => {
    const map = new Map(options.map((o) => [o.value, o.label]));
    return (v: string) => map.get(v) ?? v;
  }, [options]);

  // FIRST TWO AND A COUNT. Listing every choice overflows the row and
  // truncates mid-word, which reads as broken rather than as summary.
  const summary =
    value.length === 0
      ? placeholder
      : value.length <= 2
        ? value.map(labelFor).join(", ")
        : `${value.slice(0, 2).map(labelFor).join(", ")}  +${value.length - 2}`;

  const toggle = (option: string) => {
    if (!multiple) {
      onChange([option]);
      setOpen(false);
      return;
    }
    onChange(value.includes(option) ? value.filter((v) => v !== option) : [...value, option]);
  };

  return (
    <View style={styles.field}>
      <Text style={[styles.label, { color: theme.colors.onSurface }]}>{label}</Text>

      <Pressable
        onPress={() => setOpen(true)}
        style={({ pressed }) => [
          styles.control,
          {
            borderColor: value.length ? theme.colors.primary : theme.colors.outline,
            backgroundColor: pressed ? theme.colors.surfaceVariant : "transparent",
          },
        ]}
        accessibilityRole="button"
        accessibilityLabel={`${label}. ${value.length ? summary : placeholder}. Opens a list.`}
      >
        <Text
          numberOfLines={1}
          style={[
            styles.value,
            { color: value.length ? theme.colors.onSurface : theme.colors.onSurfaceVariant },
          ]}
        >
          {summary}
        </Text>
        <ChevronDown size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
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
            <Text style={[styles.sheetTitle, { color: theme.colors.onSurface }]}>
              {sheetTitle ?? label}
            </Text>
            {/* SAYS SO IN WORDS AS WELL AS IN SHAPE. The boxes below
                carry it, but a one-line instruction costs nothing and
                removes the question entirely -- and somebody who has
                just met a chip wall arrives expecting one answer. */}
            <Text style={[styles.sheetHint, { color: theme.colors.onSurfaceVariant }]}>
              {multiple ? "Choose as many as you like" : "Choose one"}
            </Text>

            <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
              {options.map((option) => {
                const selected = value.includes(option.value);
                return (
                  <Pressable
                    key={option.value}
                    onPress={() => toggle(option.value)}
                    style={({ pressed }) => [
                      styles.row,
                      pressed && { backgroundColor: theme.colors.surfaceVariant },
                    ]}
                    accessibilityRole={multiple ? "checkbox" : "radio"}
                    accessibilityState={{ checked: selected, selected }}
                    accessibilityLabel={option.label}
                  >
                    {/* AN EMPTY BOX IS THE WHOLE POINT. Showing a tick
                        only once something is chosen means an untouched
                        list looks like a list of links -- nothing says
                        how many answers it wants. Mandla hit exactly
                        that: "the UI is not clear... like a box there,
                        to show we can select multiple".

                        SQUARE FOR MANY, CIRCLE FOR ONE, which is the
                        one convention people already read without being
                        told, and it distinguishes the two kinds of
                        question before a single tap. */}
                    <View
                      style={[
                        styles.box,
                        multiple ? styles.boxSquare : styles.boxRound,
                        {
                          borderColor: selected ? theme.colors.primary : theme.colors.outline,
                          backgroundColor: selected ? theme.colors.primary : "transparent",
                        },
                      ]}
                    >
                      {selected &&
                        (multiple ? (
                          <Check size={14} color={theme.colors.onPrimary} strokeWidth={3.5} />
                        ) : (
                          <View
                            style={[styles.dot, { backgroundColor: theme.colors.onPrimary }]}
                          />
                        ))}
                    </View>

                    <Text
                      style={[
                        styles.rowLabel,
                        {
                          color: selected ? theme.colors.onSurface : theme.colors.onSurface,
                          fontWeight: selected ? "700" : "500",
                        },
                      ]}
                    >
                      {option.label}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            {/* ONLY FOR MULTI-SELECT. A single choice dismisses itself,
                so a Done button there would be a second tap that
                changes nothing. */}
            {multiple && (
              <Pressable
                onPress={() => setOpen(false)}
                style={[styles.done, { backgroundColor: theme.colors.primary }]}
                accessibilityRole="button"
                accessibilityLabel={
                  value.length ? `Done, ${value.length} selected` : "Done"
                }
              >
                <Text style={[styles.doneText, { color: theme.colors.onPrimary }]}>
                  {value.length ? `Done  ·  ${value.length} selected` : "Done"}
                </Text>
              </Pressable>
            )}
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

/**
 * SelectField for a question with exactly one answer.
 *
 * SelectField itself always speaks in arrays, so that switching a
 * question between one answer and several is a prop rather than a
 * rewrite. That is right for the component and tedious at the call
 * site, where most questions have one answer and every one of them
 * would otherwise carry the same `value ? [value] : []` and
 * `onChange(v[0])` noise. This holds that conversion once.
 */
export function SingleSelectField<T extends string>({
  label,
  options,
  value,
  onChange,
  placeholder,
  sheetTitle,
}: {
  label: string;
  options: SelectOption[];
  value: T | undefined;
  onChange: (value: T | undefined) => void;
  placeholder?: string;
  sheetTitle?: string;
}) {
  return (
    <SelectField
      label={label}
      options={options}
      value={value ? [value] : []}
      onChange={(next) => onChange(next[0] as T | undefined)}
      placeholder={placeholder}
      sheetTitle={sheetTitle}
    />
  );
}

const ROW_HEIGHT = 52;

const styles = StyleSheet.create({
  field: { gap: spacing.xs },
  label: { ...typography.body, fontWeight: "600" },
  control: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    borderWidth: 1.5,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    minHeight: 52,
  },
  value: { ...typography.body, flex: 1 },
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.45)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    // CAPPED AT 80% so the sheet always reads as a sheet -- a
    // full-height one is a screen, and a person loses the sense that
    // dismissing it returns them to the form underneath.
    maxHeight: "80%",
  },
  grabber: { alignSelf: "center", width: 36, height: 4, borderRadius: 2, marginBottom: spacing.sm },
  sheetTitle: {
    ...typography.h2,
    fontWeight: "700",
    marginLeft: spacing.sm,
  },
  sheetHint: { ...typography.bodySmall, marginLeft: spacing.sm, marginBottom: spacing.sm },
  list: { flexGrow: 0 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    minHeight: ROW_HEIGHT,
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
  },
  // ON THE LEFT, where a checklist puts it. On the right it reads as a
  // confirmation of something already done rather than as a control
  // you are being offered.
  box: {
    width: 22,
    height: 22,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  boxSquare: { borderRadius: 6 },
  boxRound: { borderRadius: 11 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  rowLabel: { ...typography.body, flex: 1 },
  done: {
    marginTop: spacing.sm,
    minHeight: 50,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  doneText: { ...typography.body, fontWeight: "700" },
});
