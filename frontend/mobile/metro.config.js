// Metro config — extends Expo's default so it can bundle the two
// downloadable Bulk Products documents (assets/bulk-import/) as real
// binary assets. Metro's default assetExts covers images/fonts/etc.
// but not .xlsx/.docx, so without this they'd be (incorrectly) treated
// as source files Metro tries to parse as JS and fails on.
const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

config.resolver.assetExts.push("xlsx", "docx");

module.exports = config;
