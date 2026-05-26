import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';

const html = readFileSync(new URL('../turkey_map.html', import.meta.url), 'utf8');
const markdown = readFileSync(new URL('../turkey_trip_2026.md', import.meta.url), 'utf8').trim();

test('general information control is rendered above the satellite control', () => {
  const controls = html.match(/<div id="ctrls">([\s\S]*?)<\/div>/);

  assert.ok(controls, 'map controls block should exist');
  assert.match(controls[1], /id="btn-info"/);
  assert.match(controls[1], /onclick="openInfoModal\(\)"/);
  assert.match(controls[1], />ℹ️ Общая информация<\/button>/);
  assert.ok(
    controls[1].indexOf('id="btn-info"') < controls[1].indexOf('id="btn-sat"'),
    'general information button should be above the satellite button',
  );
});

test('general information modal embeds the full markdown source', () => {
  assert.match(html, /id="info-modal"/);
  assert.match(html, /id="info-content"/);
  assert.match(html, /onclick="closeInfoModal\(\)"/);
  assert.match(html, /function openInfoModal\(\)/);
  assert.match(html, /function closeInfoModal\(\)/);

  const source = html.match(
    /<script type="text\/plain" id="trip-info-source">([\s\S]*?)<\/script>/,
  );

  assert.ok(source, 'trip info markdown source should be embedded in the page');
  assert.equal(source[1].trim(), markdown);
});
