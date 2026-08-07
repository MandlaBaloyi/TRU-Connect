/**
 * Ambient type declaration for `process.env` — Expo's babel plugin
 * statically replaces `process.env.EXPO_PUBLIC_X` expressions at build
 * time (see loanBookApi.ts's own comment on this), but TypeScript still
 * needs to know what `process` and `process.env` actually look like at
 * the SOURCE level, before that replacement happens. This declares it
 * directly rather than depending on @types/node, so it works regardless
 * of whether that package is installed.
 */
declare const process: {
  env: {
    EXPO_PUBLIC_API_BASE_URL?: string;
    EXPO_PUBLIC_USE_MOCK_API?: string;
    EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?: string;
    EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID?: string;
    EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?: string;
    [key: string]: string | undefined;
  };
};