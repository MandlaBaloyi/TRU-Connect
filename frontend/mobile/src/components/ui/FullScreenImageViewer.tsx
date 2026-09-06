import React from "react";
import { Dimensions, Image, Modal, Pressable, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Gesture, GestureDetector, GestureHandlerRootView } from "react-native-gesture-handler";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { X } from "lucide-react-native";

/**
 * Fullscreen image viewer -- pinch to zoom, drag to pan while zoomed,
 * double-tap to toggle zoom, X (or Android back) to close. Used from
 * the Profile screen's image action sheet ("View photo").
 *
 * Deliberately minimal: no swipe-to-dismiss (it fights the pan gesture
 * for little gain when there's already a close button and hardware
 * back). Image is shown `contain` so any aspect ratio the supplier
 * uploaded is seen whole.
 */
const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get("window");
const MAX_SCALE = 4;

interface Props {
  visible: boolean;
  uri: string | null;
  onClose: () => void;
}

export function FullScreenImageViewer({ visible, uri, onClose }: Props) {
  const insets = useSafeAreaInsets();

  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const savedTranslateX = useSharedValue(0);
  const savedTranslateY = useSharedValue(0);

  // Shared-value writes only ever happen on one thread. Reset is
  // inlined into each place it's needed rather than a cross-worklet
  // call, to keep the reanimated babel handling trivial.
  const resetFromJS = () => {
    scale.value = withTiming(1);
    savedScale.value = 1;
    translateX.value = withTiming(0);
    translateY.value = withTiming(0);
    savedTranslateX.value = 0;
    savedTranslateY.value = 0;
  };

  const pinch = Gesture.Pinch()
    .onUpdate((e) => {
      scale.value = Math.min(Math.max(savedScale.value * e.scale, 1), MAX_SCALE);
    })
    .onEnd(() => {
      if (scale.value <= 1) {
        scale.value = withTiming(1);
        savedScale.value = 1;
        translateX.value = withTiming(0);
        translateY.value = withTiming(0);
        savedTranslateX.value = 0;
        savedTranslateY.value = 0;
      } else {
        savedScale.value = scale.value;
      }
    });

  const pan = Gesture.Pan()
    .minPointers(1)
    .onUpdate((e) => {
      if (scale.value <= 1) return;
      translateX.value = savedTranslateX.value + e.translationX;
      translateY.value = savedTranslateY.value + e.translationY;
    })
    .onEnd(() => {
      savedTranslateX.value = translateX.value;
      savedTranslateY.value = translateY.value;
    });

  const doubleTap = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      if (scale.value > 1) {
        scale.value = withTiming(1);
        savedScale.value = 1;
        translateX.value = withTiming(0);
        translateY.value = withTiming(0);
        savedTranslateX.value = 0;
        savedTranslateY.value = 0;
      } else {
        scale.value = withTiming(2.5);
        savedScale.value = 2.5;
      }
    });

  const composed = Gesture.Simultaneous(pinch, pan, doubleTap);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
      { scale: scale.value },
    ],
  }));

  const handleClose = () => {
    resetFromJS();
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" statusBarTranslucent onRequestClose={handleClose}>
      {/* A Modal renders in its own native hierarchy, OUTSIDE the root
          GestureHandlerRootView -- gestures inside it are dead without
          this local root. */}
      <GestureHandlerRootView style={styles.container}>
        {uri && (
          <GestureDetector gesture={composed}>
            <Animated.View style={[styles.imageWrap, animatedStyle]}>
              <Image source={{ uri }} style={styles.image} resizeMode="contain" />
            </Animated.View>
          </GestureDetector>
        )}

        <Pressable
          onPress={handleClose}
          style={[styles.closeButton, { top: insets.top + 8 }]}
          hitSlop={12}
          accessibilityRole="button"
          accessibilityLabel="Close image"
        >
          <X size={24} color="#fff" strokeWidth={2.4} />
        </Pressable>
      </GestureHandlerRootView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000", alignItems: "center", justifyContent: "center" },
  imageWrap: { width: SCREEN_W, height: SCREEN_H, alignItems: "center", justifyContent: "center" },
  image: { width: SCREEN_W, height: SCREEN_H },
  closeButton: {
    position: "absolute",
    right: 12,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
  },
});
