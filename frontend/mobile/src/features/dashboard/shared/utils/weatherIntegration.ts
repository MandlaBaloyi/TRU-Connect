/**
 * Reserved integration point for weather providers.
 * Ref: master prompt "External API Ready > Weather APIs (Future)" --
 * Agriculture, Delivery Planning.
 * Not implemented yet -- no current screen calls this.
 */
export async function getWeatherForecast(_latitude: number, _longitude: number): Promise<never> {
  throw new Error(
    "weatherIntegration.getWeatherForecast is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}
