import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';

const html = readFileSync(new URL('../turkey_map.html', import.meta.url), 'utf8');
const swUrl = new URL('../sw.js', import.meta.url);
const manifestUrl = new URL('../manifest.webmanifest', import.meta.url);
const gpxUrl = new URL('../turkey-route-2026.gpx', import.meta.url);
const kmlUrl = new URL('../turkey-route-2026.kml', import.meta.url);
const indexUrl = new URL('../index.html', import.meta.url);

const sw = existsSync(swUrl) ? readFileSync(swUrl, 'utf8') : '';

test('app shell uses local assets and registers a file-based service worker', () => {
  assert.match(html, /<link rel="manifest" href="manifest\.webmanifest">/);
  assert.match(html, /href="vendor\/leaflet\/leaflet\.css"/);
  assert.match(html, /src="vendor\/leaflet\/leaflet\.js"/);
  assert.match(html, /navigator\.serviceWorker\.register\(['"]\.\/sw\.js['"]\)/);

  assert.doesNotMatch(html, /https:\/\/unpkg\.com\/leaflet/);
  assert.doesNotMatch(html, /URL\.createObjectURL\(blob\)/);
  assert.doesNotMatch(html, /new Blob\(\[swCode\]/);
});

test('service worker precaches the app shell and caches map tiles for offline reuse', () => {
  assert.ok(existsSync(swUrl), 'sw.js should exist');
  assert.match(sw, /turkey_map\.html/);
  assert.match(sw, /vendor\/leaflet\/leaflet\.css/);
  assert.match(sw, /vendor\/leaflet\/leaflet\.js/);
  assert.match(sw, /event\.request\.mode\s*===\s*['"]navigate['"]/);
  assert.match(sw, /caches\.match\(['"]\.\/turkey_map\.html['"]/);
  assert.match(sw, /tile\.openstreetmap\.org/);
  assert.match(sw, /basemaps\.cartocdn\.com/);
  assert.match(sw, /arcgisonline\.com/);
  assert.match(sw, /response\.ok\s*\|\|\s*response\.type\s*===\s*['"]opaque['"]/);
});

test('manifest and offline navigator export files are present', () => {
  assert.ok(existsSync(manifestUrl), 'manifest.webmanifest should exist');
  assert.ok(existsSync(gpxUrl), 'GPX export should exist');
  assert.ok(existsSync(kmlUrl), 'KML export should exist');

  assert.match(html, /href="turkey-route-2026\.gpx"/);
  assert.match(html, /href="turkey-route-2026\.kml"/);
  assert.match(html, /https:\/\/osmand\.net\/map\/navigate\//);
  assert.match(html, /https:\/\/omaps\.app\/v2\/nav/);
});

test('site root forwards visitors to the map entrypoint', () => {
  assert.ok(existsSync(indexUrl), 'index.html should exist for static hosting root URLs');

  const index = readFileSync(indexUrl, 'utf8');
  assert.match(index, /url=turkey_map\.html/);
  assert.match(index, /href="turkey_map\.html"/);
});
