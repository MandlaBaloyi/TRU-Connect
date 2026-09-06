/**
 * buildMapPickerHtml -- the ONE place that knows Mapbox GL JS exists.
 * MapPickerModal.tsx never imports any map library directly; it just
 * hands this HTML string to a WebView, same isolation shape as the
 * backend's own provider pattern (one thing owns the vendor SDK, one
 * thing owns the interface everyone else depends on).
 *
 * CDN VERSION confirmed directly against Mapbox's own current "Get
 * Started with a CDN" docs before writing this, not carried over from
 * training data -- see the docs.mapbox.com getting-started guide.
 *
 * THE PIN NEVER MOVES ON SCREEN -- it's a plain CSS element fixed to
 * the center of the page, drawn OVER the map, not a real Mapbox
 * marker tied to a coordinate. The MAP moves underneath it as the
 * user pans (Uber's own pickup-pin pattern, confirmed as the intended
 * design). On the map's `moveend` event, this page reads
 * map.getCenter() -- genuinely just "what coordinate is currently
 * under the fixed pin" -- and posts it back to React Native. That
 * coordinate is real map-interaction data, never a Mapbox geocoding
 * API result, which is what keeps this feature outside Mapbox's
 * storage-licensing rules by design (see the backend geocoding
 * module's own docstring for the full reasoning).
 *
 * Rotation/pitch disabled deliberately -- a spaza owner dropping a
 * pin needs "pan to the right spot", not a 3D tilt control they could
 * get lost in.
 *
 * NO RN -> WEBVIEW COMMANDS -- an earlier version of this had a
 * window.flyTo() the React Native side could call via
 * injectJavaScript, for when a Search Box suggestion was picked while
 * this map was already open. That combined layout is gone (see
 * MapPickerModal's own docstring on SearchAddressModal) -- a search
 * result now seeds MapPickerModal's initialLatitude/initialLongitude
 * BEFORE this page is ever created, so there's never a need to
 * re-center an already-running map. One direction of communication
 * (WebView -> React Native, via postMessage) is all this needs.
 */
export function buildMapPickerHtml(
  accessToken: string,
  initialLatitude: number,
  initialLongitude: number,
  initialZoom: number = 15
): string {
  return `<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
<script src="https://api.mapbox.com/mapbox-gl-js/v3.18.1/mapbox-gl.js"></script>
<link href="https://api.mapbox.com/mapbox-gl-js/v3.18.1/mapbox-gl.css" rel="stylesheet" />
<style>
  html, body, #map { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
  #pin {
    position: absolute;
    top: 50%;
    left: 50%;
    /* Anchored at the pin's own tip, not its center, so the TIP
       (not the whole icon) marks the real coordinate underneath it. */
    transform: translate(-50%, -100%);
    width: 32px;
    height: 32px;
    pointer-events: none;
    z-index: 10;
  }
  #pin svg { width: 100%; height: 100%; }
</style>
</head>
<body>
<div id="map"></div>
<div id="pin">
  <svg viewBox="0 0 24 24" fill="none" stroke="#D85A30" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
    <circle cx="12" cy="10" r="3"/>
  </svg>
</div>
<script>
  mapboxgl.accessToken = ${JSON.stringify(accessToken)};
  const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [${initialLongitude}, ${initialLatitude}],
    zoom: ${initialZoom},
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
  });
  map.touchZoomRotate.disableRotation();

  function postCenter() {
    const center = map.getCenter();
    if (window.ReactNativeWebView) {
      window.ReactNativeWebView.postMessage(JSON.stringify({
        type: 'center',
        latitude: center.lat,
        longitude: center.lng,
      }));
    }
  }

  map.on('load', postCenter);
  map.on('moveend', postCenter);
</script>
</body>
</html>`;
}
