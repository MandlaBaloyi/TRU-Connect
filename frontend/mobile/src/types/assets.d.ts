/**
 * Ambient declarations for asset file types Metro can bundle but
 * TypeScript doesn't know about out of the box -- unlike .png/.jpg
 * (covered by React Native's own built-in types), .xlsx/.docx have no
 * default declaration, so `require("./file.xlsx")` would otherwise
 * fail to compile. Registered as bundleable via metro.config.js;
 * this file is what makes the TypeScript side of that work too.
 */

declare module "*.xlsx" {
  const moduleId: number;
  export = moduleId;
}

declare module "*.docx" {
  const moduleId: number;
  export = moduleId;
}
