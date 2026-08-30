import { Linking } from "react-native";

export function buildTikTokUrl(handle: string): string {
  return `https://www.tiktok.com/@${handle}`;
}

export function openUrl(url: string) {
  Linking.openURL(url).catch(() => {
    // Silently ignored, same reasoning as ContactActionsRow.tsx's own
    // handlers: wa.me and tiktok.com both degrade to a normal web page
    // when the native app isn't installed, so a failure here means no
    // URL at all could be opened (no network route) -- nothing more
    // useful to do than leave the screen as it was.
  });
}
