import React, { useEffect, useRef } from "react";
import { Animated } from "react-native";

/**
 * Fades its children in once, on mount.
 *
 * BUILT FOR THE COLLAPSING PROFILE HEADER, where the supplier's name
 * and avatar appear in the top bar as the brand header scrolls away.
 * That swap is driven by a boolean rather than a scroll-linked
 * animation (see SupplierProfileScreen on why: rebuilding header
 * options sixty times a second is not worth it), so without this the
 * identity would pop into existence in one frame.
 *
 * useNativeDriver, so the fade runs on the UI thread and keeps going
 * smoothly even while JS is busy laying out the rest of the screen --
 * which, mid-scroll on a long profile, it usually is.
 *
 * 160ms: long enough to read as an arrival rather than a glitch,
 * short enough that a fast scroller is never waiting for it.
 */
export function FadeIn({ children, duration = 160 }: { children: React.ReactNode; duration?: number }) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.timing(opacity, {
      toValue: 1,
      duration,
      useNativeDriver: true,
    });
    animation.start();
    // Stopped rather than left running: this mounts inside a header
    // that can be replaced mid-animation when the screen changes.
    return () => animation.stop();
  }, [opacity, duration]);

  return <Animated.View style={{ opacity }}>{children}</Animated.View>;
}
