// test-q3n-parser.js — Tests for q3n-parser.js
// Run: node test-q3n-parser.js

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const Q3NParser = require('./q3n-parser');

const SAMPLE = `#!q3n-format

/// https://example.com/article
The quick brown fox jumps over the lazy dog.
This is a second line of the quote.
\\\\\\

/// isbn://978-0-13-468599-1;The_Pragmatic_Programmer;Andy_Hunt;1999 /// book:
Software is a creative process.
\\\\\\

/// q3n://author:john;john@example.com;'John Doe' /// person:
A person reference entry.
\\\\\\
`;

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ✗ ${name}`);
    console.log(`    ${e.message}`);
  }
}

console.log('\n# Q3N Parser — JavaScript Tests\n');

// ── Basic Parsing ──

test('parse returns correct number of entries', () => {
  const entries = Q3NParser.parse(SAMPLE);
  assert.strictEqual(entries.length, 3);
});

test('parse web entry', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const e = entries[0];
  assert.strictEqual(e.scheme, 'https');
  assert.strictEqual(e.uri, 'https://example.com/article');
  assert.ok(e.quote.includes('quick brown fox'));
  assert.strictEqual(e.tag, null);
});

test('parse isbn entry', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const e = entries[1];
  assert.strictEqual(e.scheme, 'isbn');
  assert.strictEqual(e.tag, 'book');
});

test('parse person entry', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const e = entries[2];
  assert.strictEqual(e.scheme, 'q3n');
  assert.strictEqual(e.tag, 'person');
});

test('parse empty returns empty array', () => {
  assert.deepStrictEqual(Q3NParser.parse(''), []);
});

// ── URI Parsing ──

test('parse web URI with fragment', () => {
  const meta = Q3NParser.URI_PARSERS.https('https://example.com/page#section-3');
  assert.strictEqual(meta.domain, 'example.com');
  assert.strictEqual(meta.fragment, 'section-3');
});

test('parse q3n URI', () => {
  const meta = Q3NParser.URI_PARSERS.q3n("q3n://john:123;email@test.com;'John Smith'");
  assert.strictEqual(meta.type, 'person');
  assert.strictEqual(meta.handle, 'john');
  assert.strictEqual(meta.name, 'John Smith');
});

test('parse isbn URI', () => {
  const meta = Q3NParser.URI_PARSERS.isbn('isbn://978-0-13-468599-1;Title;Author;2024');
  assert.strictEqual(meta.isbn, '978-0-13-468599-1');
  assert.strictEqual(meta.title, 'Title');
  assert.strictEqual(meta.author, 'Author');
  assert.strictEqual(meta.year, 2024);
});

test('parse doi URI', () => {
  const meta = Q3NParser.URI_PARSERS.doi('doi://10.1000/xyz123');
  assert.strictEqual(meta.doi, '10.1000/xyz123');
});

test('parse arxiv URI', () => {
  const meta = Q3NParser.URI_PARSERS.arxiv('arxiv://2301.00001');
  assert.strictEqual(meta.arxivId, '2301.00001');
});

test('parse yt URI with timestamp', () => {
  const meta = Q3NParser.URI_PARSERS.yt('yt://dQw4w9WgXcQ?t=42');
  assert.strictEqual(meta.videoId, 'dQw4w9WgXcQ');
  assert.strictEqual(meta.timestamp, 42);
});

test('parse pubmed URI', () => {
  const meta = Q3NParser.URI_PARSERS.pubmed('pubmed://12345678');
  assert.strictEqual(meta.type, 'academic');
  assert.strictEqual(meta.pmid, '12345678');
});

test('parse orcid URI', () => {
  const meta = Q3NParser.URI_PARSERS.orcid('orcid://0000-0002-1825-0097');
  assert.strictEqual(meta.type, 'person');
  assert.strictEqual(meta.orcid, '0000-0002-1825-0097');
});

test('parse spotify URI track', () => {
  const meta = Q3NParser.URI_PARSERS.spotify('spotify://track:4cOdK2wGLETKBW3PvgPWqT');
  assert.strictEqual(meta.type, 'media');
  assert.strictEqual(meta.kind, 'track');
  assert.strictEqual(meta.id, '4cOdK2wGLETKBW3PvgPWqT');
});

test('parse spotify URI bare', () => {
  const meta = Q3NParser.URI_PARSERS.spotify('spotify://4cOdK2wGLETKBW3PvgPWqT');
  assert.strictEqual(meta.id, '4cOdK2wGLETKBW3PvgPWqT');
  assert.ok(!meta.kind);
});

// ── Content Type Detection ──

test('detect content type: text', () => {
  assert.strictEqual(Q3NParser.detectContentType('Just a regular quote.'), 'text');
});

test('detect content type: json', () => {
  assert.strictEqual(Q3NParser.detectContentType('{"key": "value"}'), 'json');
});

test('detect content type: code', () => {
  assert.strictEqual(Q3NParser.detectContentType('def hello():\n  return 42'), 'code');
});

// ── Attribution ──

test('attribution for web entry', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const attr = entries[0].attribution();
  assert.ok(attr.includes('example.com'));
});

test('attribution for q3n entry', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const attr = entries[2].attribution();
  assert.ok(attr.includes('John Doe'));
});

test('attribution for pubmed entry', () => {
  const [scheme, path] = Q3NParser.parse('/// pubmed://12345678\nResult.\n\\\\\\')[0] ?
    [Q3NParser.parse('/// pubmed://12345678\nResult.\n\\\\\\')[0].scheme,
     Q3NParser.parse('/// pubmed://12345678\nResult.\n\\\\\\')[0].path] : ['', ''];
  const e = new Q3NParser.Q3NEntry('pubmed://12345678', 'pubmed', '12345678', 'Result.');
  assert.ok(e.attribution().includes('pubmed'));
});

test('attribution for orcid entry', () => {
  const e = new Q3NParser.Q3NEntry('orcid://0000-0002-1825-0097', 'orcid', '0000-0002-1825-0097', 'Cited.');
  assert.ok(e.attribution().includes('0000-0002-1825-0097'));
});

test('attribution for spotify entry', () => {
  const e = new Q3NParser.Q3NEntry('spotify://track:abc', 'spotify', 'track:abc', 'Lyric.');
  assert.ok(e.attribution().includes('Spotify'));
  assert.ok(e.attribution().includes('track'));
});

test('SCHEME_CATEGORIES includes new schemes', () => {
  assert.strictEqual(Q3NParser.SCHEME_CATEGORIES.pubmed, 'academic');
  assert.strictEqual(Q3NParser.SCHEME_CATEGORIES.orcid, 'person');
  assert.strictEqual(Q3NParser.SCHEME_CATEGORIES.spotify, 'media');
});

test('parse inline \\\\\\  variant', () => {
  const text = '/// https://example.com\nquote text\\\\\\';
  const entries = Q3NParser.parse(text);
  assert.strictEqual(entries.length, 1);
  assert.strictEqual(entries[0].quote, 'quote text');
});

// ── Detection ──

test('detect by content header', () => {
  assert.ok(Q3NParser.detectContent('#!q3n-format\n'));
});

test('detect by start pattern', () => {
  assert.ok(Q3NParser.detectContent('/// https://example.com\nquote\n\\\\\\\n'));
});

test('detect non-q3n content', () => {
  assert.ok(!Q3NParser.detectContent('Just some text.'));
});

// ── Serialization ──

test('serialize roundtrip', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const output = Q3NParser.serialize(entries);
  const reParsed = Q3NParser.parse(output);
  assert.strictEqual(reParsed.length, entries.length);
  reParsed.forEach((e, i) => {
    assert.strictEqual(e.uri, entries[i].uri);
    assert.strictEqual(e.quote, entries[i].quote);
  });
});

// ── Export ──

test('export JSON', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const json = Q3NParser.exportJson(entries);
  const data = JSON.parse(json);
  assert.strictEqual(data.length, 3);
});

// ── Fortune ──

test('export fortune format', () => {
  const entries = Q3NParser.parse(SAMPLE);
  const text = Q3NParser.exportFortune(entries);
  assert.ok(text.includes('%'));
  assert.strictEqual(text.split('%').length - 1, 3);
});

// ── Summary ──

console.log(`\n${passed} passed, ${failed} failed, ${passed + failed} total\n`);
process.exit(failed ? 1 : 0);
