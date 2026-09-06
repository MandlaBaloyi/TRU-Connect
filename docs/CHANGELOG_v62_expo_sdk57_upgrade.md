# v62 — Expo SDK 54 → 57 upgrade

Real dependency upgrade, not a version-number-only bump. Expo Go on your device auto-updated to require SDK 57; this brings the project to match, going forward rather than pinning Expo Go back.

## What actually happened

Jumped three SDK releases (54 → 55 → 56 → 57), so this wasn't the "one command, no breaking changes" upgrade Expo describes for 56→57 alone — real breakage from the accumulated three-release gap had to be found and fixed, not just dependency versions bumped.

**The source of truth for every version below**: `node_modules/expo/bundledNativeModules.json`, which ships *inside* the installed `expo` package itself — the real, authoritative compatibility manifest for exactly SDK 57.0.20, not a guess. `npx expo install --fix` (Expo's own recommended tool) couldn't run in this sandbox — it needs to reach `api.expo.dev`, which this environment's network allowlist doesn't include — so every version below was set by hand against that same real manifest instead of the live tool, which comes to the identical result.

## Dependency changes
- `expo`: `~54.0.35` → `^57.0.20`
- `react`: `19.1.0` → `^19.2.3`, `react-native`: `0.81.5` → `^0.86.3`
- `@types/react`: `~19.1.0` → `~19.2.0` (matching React 19.2)
- Every `expo-*` package bumped to its exact SDK 57 compatible version (asset, camera, constants, document-picker, file-system, font, image-picker, linear-gradient, linking, local-authentication, location, router, secure-store, sharing, status-bar, system-ui)
- `babel-preset-expo`: `~54.0.10` → `~57.0.10` (this package's own version numbers track the Expo SDK number directly)
- `react-native-reanimated` → `4.5.1`, `react-native-worklets` → `0.10.1`, `react-native-gesture-handler` → `~2.32.0`, `react-native-screens` → `~4.26.0`, `react-native-safe-area-context` → `~5.7.0`, `react-native-svg` → `15.15.4`, `react-native-view-shot` → `5.1.0`, `react-native-webview` → `13.16.1`, `react-native-pager-view` → `8.0.2`

## app.json
- Removed `newArchEnabled` — SDK 57 dropped the key from the schema entirely (new architecture is the only architecture now, nothing to toggle).
- Removed `edgeToEdgeEnabled` from the android config — mandatory since SDK 55, the explicit key is redundant.

## Real breakage found and fixed (not just version bumps)

1. **`@react-navigation/native-stack` type conflict** — `FeatureHeader.tsx` imported `NativeStackHeaderProps` from the raw `@react-navigation/native-stack` package. Since `expo-router` 56+ ships its *own* internal copy of these types rather than depending on that package, having both installed created a duplicate-type conflict across every single `_layout.tsx` in the app (18 near-identical errors). Fixed by importing the type from `expo-router` itself instead — the correct source now.
2. **`StyleSheet.absoluteFillObject` removed from the type declarations** (RN 0.86) — fixed in 3 files (`ScanCodeTab.tsx` ×2, `SupplierCatalogProductCard.tsx`). Direct style-prop usage switched to `StyleSheet.absoluteFill`; usage spread into a custom style object switched to the raw `{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0 }` values instead, to sidestep any ambiguity about what `absoluteFill` actually is under the hood.
3. **`ColorSchemeName` now includes `"unspecified"`** (RN 0.85+) — `useColorScheme.ts` only handled `null`/`undefined`, not this new real value. Fixed to fall back to the same default for all three.
4. **Implicit-`any` regression in `DashboardTabBar.tsx`** — `state.routes.map((route, index) => ...)` stopped inferring types after the React/RN bump. Fixed with an explicit indexed type off `state.routes` itself.

## Verified
- `npx tsc --noEmit` — back to the exact same 15-error baseline that existed before this upgrade (all in unrelated files this upgrade never touched), zero new errors.
- `npx expo-doctor` — 19/20 real checks pass (21st and 22nd both fail only because they need `api.expo.dev`, unreachable from this sandbox — not a real project issue).


