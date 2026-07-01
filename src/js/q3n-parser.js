/**
 * q3n-parser.js — JavaScript implementation of Q3N (Quote Triple-Slash Notation)
 *
 * Parses, serializes, detects, and resolves Q3N-formatted text with
 * scheme-specific URI parsers (https, http, q3n, isbn, doi, arxiv, file, yt,
 * pubmed, orcid, spotify, osm, geo, overpass).
 *
 * Usage (Node.js CLI):
 *   node q3n-parser.js extract <file>    Extract Q3N snippets
 *   node q3n-parser.js validate <file>   Validate Q3N syntax
 *   node q3n-parser.js json <file>       Output as JSON
 *   node q3n-parser.js fortune <file>    Display random fortune
 *
 * Browser:
 *   <script src="q3n-parser.js"></script>
 *   const results = Q3NParser.extract(text);
 */

const SCHEME_CATEGORIES = {
  https: 'web', http: 'web',
  q3n: 'person',
  isbn: 'book',
  doi: 'academic',
  arxiv: 'academic',
  pubmed: 'academic',
  orcid: 'person',
  file: 'file',
  yt: 'media',
  youtube: 'media',
  spotify: 'media',
  osm: 'map',
  geo: 'map',
  overpass: 'map',
  wikipedia: 'web',
  github: 'web',
};

const RECOGNIZED_EXTENSIONS = ['.q3n', '.q3nt', '.quotation', '.quotes'];

// ── Content type detection ─────────────────────────────────────────────

function detectContentType(quote) {
  const stripped = quote.trim();
  if (!stripped) return 'text';
  if (stripped.startsWith('{') && stripped.endsWith('}')) {
    try {
      JSON.parse(stripped);
      return 'json';
    } catch (_) { /* not valid JSON */ }
  }
  if (stripped.startsWith('```') || /^(def |class |import |fn |func |function |let |const |var |print\()/.test(stripped)) {
    return 'code';
  }
  const lines = stripped.split('\n');
  const codeKeywords = ['def ', 'class ', 'import ', 'from ', 'return ',
    '#include', 'fn ', 'func ', 'function ', 'let ', 'const ', 'var ', 'print('];
  const codeLines = lines.filter(l => codeKeywords.some(k => l.startsWith(k))).length;
  if (lines.length > 2 && codeLines / lines.length > 0.3) return 'code';
  return 'text';
}

// ── URI parsing helpers ────────────────────────────────────────────────

function parseScheme(uri) {
  const idx = uri.indexOf('://');
  if (idx !== -1) return [uri.slice(0, idx), uri.slice(idx + 3)];
  // Colon-only scheme (e.g. geo:51.5074,-0.1278)
  const colon = uri.indexOf(':');
  if (colon !== -1) {
    const scheme = uri.slice(0, colon);
    if (/^[a-zA-Z][a-zA-Z0-9+\-.]*$/.test(scheme)) return [scheme, uri.slice(colon + 1)];
  }
  return ['', uri];
}

function parseWebUri(uri) {
  try {
    const url = new URL(uri);
    const result = { domain: url.hostname };
    if (url.hash) result.fragment = url.hash.slice(1);
    if (url.search) {
      const params = {};
      url.searchParams.forEach((v, k) => {
        if (!params[k]) params[k] = v;
        else if (Array.isArray(params[k])) params[k].push(v);
        else params[k] = [params[k], v];
      });
      result.queryParams = params;
    }
    return result;
  } catch (_) {
    return { domain: uri.replace(/https?:\/\//, '').split('/')[0] };
  }
}

function parseQ3nUri(uri) {
  const parts = uri.replace('q3n://', '').split(';');
  const result = { type: 'person' };
  if (parts[0] && parts[0].includes(':')) {
    const [handle, userId] = parts[0].split(':');
    result.handle = handle;
    result.id = userId.startsWith('@') ? userId.slice(1) : userId;
  }
  if (parts.length > 1) result.email = parts[1];
  if (parts.length > 2) {
    let name = parts[2];
    if (name.startsWith("'") && name.endsWith("'")) name = name.slice(1, -1);
    result.name = name;
  }
  return result;
}

function parseIsbnUri(uri) {
  const parts = uri.replace('isbn://', '').split(';');
  const result = { type: 'book', isbn: parts[0] };
  if (parts.length > 1) {
    let title = parts[1];
    if (title.startsWith("'") && title.endsWith("'")) title = title.slice(1, -1);
    result.title = title;
  }
  if (parts.length > 2) {
    let author = parts[2];
    if (author.startsWith("'") && author.endsWith("'")) author = author.slice(1, -1);
    result.author = author;
  }
  if (parts.length > 3) {
    const year = parseInt(parts[3], 10);
    result.year = isNaN(year) ? parts[3] : year;
  }
  return result;
}

function parseDoiUri(uri) {
  return { type: 'academic', doi: uri.replace('doi://', '') };
}

function parseArxivUri(uri) {
  return { type: 'academic', arxivId: uri.replace('arxiv://', '') };
}

function parsePubmedUri(uri) {
  return { type: 'academic', pmid: uri.replace('pubmed://', '') };
}

function parseOrcidUri(uri) {
  return { type: 'person', orcid: uri.replace('orcid://', '') };
}

function parseSpotifyUri(uri) {
  const rest = uri.replace('spotify://', '');
  const result = { type: 'media', platform: 'spotify' };
  const colon = rest.indexOf(':');
  if (colon !== -1) {
    result.kind = rest.slice(0, colon);
    result.id = rest.slice(colon + 1);
  } else {
    result.id = rest;
  }
  return result;
}

function parseYtUri(uri) {
  let rest = uri.replace('yt://', '');
  const result = { type: 'media', platform: 'youtube' };
  const qIdx = rest.indexOf('?');
  if (qIdx !== -1) {
    const qs = rest.slice(qIdx + 1);
    rest = rest.slice(0, qIdx);
    const params = Object.fromEntries(new URLSearchParams(qs));
    if (params.v) result.videoId = params.v;
    if (params.t) result.timestamp = parseInt(params.t, 10) || params.t;
  }
  if (!result.videoId) result.videoId = rest;
  return result;
}

function parseFileUri(uri) {
  try {
    const url = new URL(uri);
    const result = { path: url.pathname };
    if (url.hash && url.hash.includes('line=')) {
      const line = parseInt(url.hash.split('line=')[1], 10);
      if (!isNaN(line)) result.line = line;
    }
    return result;
  } catch (_) {
    return { path: uri.replace('file://', '') };
  }
}

function parseOsmUri(uri) {
  const path = uri.replace('osm://', '');
  const parts = path.split('/');
  const objType = parts[0] || 'node';
  const objId = parts.slice(1).join('/') || '';
  return {
    type: objType,
    id: objId,
    browseUrl: `https://www.openstreetmap.org/${objType}/${objId}`,
    apiUrl: `https://api.openstreetmap.org/api/0.6/${objType}/${objId}`,
  };
}

function parseGeoUri(uri) {
  const rest = uri.replace('geo:', '');
  const qIdx = rest.indexOf('?');
  const coordStr = qIdx === -1 ? rest : rest.slice(0, qIdx);
  const result = {};
  const comma = coordStr.indexOf(',');
  if (comma !== -1) {
    const lat = parseFloat(coordStr.slice(0, comma));
    const lon = parseFloat(coordStr.slice(comma + 1));
    if (!isNaN(lat) && !isNaN(lon)) {
      result.lat = lat;
      result.lon = lon;
    }
  }
  let zoom = 14;
  if (qIdx !== -1) {
    const qs = new URLSearchParams(rest.slice(qIdx + 1));
    const z = parseInt(qs.get('z'), 10);
    if (!isNaN(z)) zoom = z;
  }
  if (result.lat !== undefined) {
    result.zoom = zoom;
    result.mapUrl = `https://www.openstreetmap.org/?mlat=${result.lat}&mlon=${result.lon}&zoom=${zoom}`;
  }
  return result;
}

function parseOverpassUri(uri) {
  const query = uri.replace('overpass://', '');
  return {
    query,
    apiUrl: `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`,
  };
}

function parseWikipediaUri(uri) {
  const rest = uri.replace('wikipedia://', '');
  const slash = rest.indexOf('/');
  let lang = null;
  let article = rest;
  if (slash !== -1) {
    const maybeLang = rest.slice(0, slash);
    if (maybeLang.length === 2) {
      lang = maybeLang;
      article = rest.slice(slash + 1);
    }
  }
  const browseUrl = lang
    ? `https://${lang}.wikipedia.org/wiki/${article}`
    : `https://en.wikipedia.org/wiki/${article}`;
  return { type: 'web', article, lang: lang || 'en', browseUrl };
}

function parseGithubUri(uri) {
  const rest = uri.replace('github://', '');
  const parts = rest.split('/');
  const owner = parts[0] || '';
  const repo = parts[1] || '';
  const kind = parts.length >= 4 ? parts[2] : null;
  const kindId = parts.length >= 4 ? parts[3] : null;
  const label = kind ? `${owner}/${repo}/${kind}/${kindId}` : `${owner}/${repo}`;
  let browseUrl = `https://github.com/${owner}/${repo}`;
  if (kind) browseUrl += `/${kind}/${kindId}`;
  return { type: 'web', platform: 'github', owner, repo, kind, id: kindId, label, browseUrl };
}

const URI_PARSERS = {
  https: parseWebUri,
  http: parseWebUri,
  q3n: parseQ3nUri,
  isbn: parseIsbnUri,
  doi: parseDoiUri,
  arxiv: parseArxivUri,
  pubmed: parsePubmedUri,
  orcid: parseOrcidUri,
  spotify: parseSpotifyUri,
  yt: parseYtUri,
  youtube: parseYtUri,
  file: parseFileUri,
  osm: parseOsmUri,
  geo: parseGeoUri,
  overpass: parseOverpassUri,
  wikipedia: parseWikipediaUri,
  github: parseGithubUri,
};

// ── Q3N Entry class ───────────────────────────────────────────────────

class Q3NEntry {
  constructor(uri, scheme, path, quote, tag) {
    this.uri = uri;
    this.scheme = scheme;
    this.path = path;
    this.quote = quote.replace(/\n$/, '');
    this.tag = tag ? tag.replace(/:$/, '') : null;
  }

  derive() {
    const r = {};
    const parser = URI_PARSERS[this.scheme];
    if (parser) {
      try { r.meta = parser(this.uri); } catch (_) {}
    }
    if (!r.meta) {
      if (this.scheme === 'https' || this.scheme === 'http') {
        try { r.meta = { domain: new URL(this.uri).hostname }; } catch (_) {}
      } else if (this.scheme === 'file') {
        r.meta = { path: this.uri.replace('file://', '') };
      }
    }
    if (SCHEME_CATEGORIES[this.scheme]) {
      r.category = SCHEME_CATEGORIES[this.scheme];
    }
    r.contentType = detectContentType(this.quote);
    return r;
  }

  toDict() {
    const d = { uri: this.uri, scheme: this.scheme, path: this.path, quote: this.quote };
    if (this.tag) d.tag = this.tag;
    Object.assign(d, this.derive());
    return d;
  }

  attribution() {
    const derived = this.derive();
    const meta = derived.meta || {};
    switch (this.scheme) {
      case 'q3n':
        if (meta.name) return `— ${meta.name}`;
        if (meta.handle) return `— @${meta.handle}`;
        if (meta.email) return `— ${meta.email}`;
        break;
      case 'isbn':
        const parts = [];
        if (meta.author) parts.push(meta.author);
        if (meta.title) parts.push(`"${meta.title}"`);
        if (meta.year) parts.push(`(${meta.year})`);
        if (parts.length) return `— ${parts.join(', ')}`;
        break;
      case 'doi': case 'arxiv': case 'pubmed':
        return `— Academic paper (${this.scheme})`;
      case 'orcid':
        if (meta.orcid) return `— ORCID ${meta.orcid}`;
        break;
      case 'spotify':
        return `— Spotify ${meta.kind || 'track'}`;
      case 'https': case 'http':
        if (meta.domain) return `— ${meta.domain}`;
        break;
      case 'yt': case 'youtube':
        return `— YouTube`;
      case 'osm':
        return `— OpenStreetMap ${meta.type || 'feature'}`;
      case 'geo':
        return meta.lat !== undefined ? `— ${meta.lat},${meta.lon}` : `— Geo coordinates`;
      case 'overpass':
        return `— Overpass API`;
      case 'wikipedia': {
        const article = (meta.article || '').replace(/_/g, ' ');
        return `— Wikipedia (${(meta.lang || 'en').toUpperCase()}): ${article}`;
      }
      case 'github':
        return `— GitHub: ${meta.label || `${meta.owner}/${meta.repo}`}`;
    }
    return `— ${this.uri}`;
  }
}

// ── Main parser (line-by-line, no backtracking) ────────────────────────

const Q3N_START = /^\/\/\/[ \t]+(.+?)(?:[ \t]+\/\/\/[ \t]+([^:\s]+):)?[ \t]*$/m;
const Q3N_END   = /^\\\\\\[ \t]*$/m;

function parse(text) {
  if (!text) return [];
  const entries = [];
  const lines = text.split('\n');
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const m = line.match(Q3N_START);
    if (m) {
      const uri = m[1];
      const tag = m[2] || null;
      const quoteLines = [];
      i++;
      let closed = false;
      while (i < lines.length) {
        if (Q3N_END.test(lines[i])) { closed = true; break; }
        // Allow \\\ at end of the last quote line (Python-compatible)
        if (lines[i].trimEnd().endsWith('\\\\\\')) {
          quoteLines.push(lines[i].trimEnd().slice(0, -3));
          closed = true;
          break;
        }
        quoteLines.push(lines[i]);
        i++;
      }
      if (closed) {
        const quote = quoteLines.join('\n').replace(/\n$/, '');
        const [scheme, path] = parseScheme(uri);
        entries.push(new Q3NEntry(uri, scheme, path, quote, tag));
      }
    }
    i++;
  }
  return entries;
}

function serialize(entries) {
  const lines = ['#!q3n-format', ''];
  for (const e of entries) {
    const tagPart = e.tag ? ` /// ${e.tag}:` : '';
    lines.push(`/// ${e.uri}${tagPart}`);
    lines.push(e.quote);
    lines.push('\\\\\\');
    lines.push('');
  }
  return lines.join('\n');
}

function detect(textOrPath) {
  if (typeof textOrPath === 'string' && !textOrPath.includes('\n')) {
    // Treat as file path
    const ext = '.' + textOrPath.split('.').pop();
    if (RECOGNIZED_EXTENSIONS.includes(ext)) return true;
    try {
      const fs = require('fs');
      const content = fs.readFileSync(textOrPath, 'utf-8');
      return detectContent(content);
    } catch (_) { return false; }
  }
  return detectContent(textOrPath);
}

function detectContent(text) {
  if (!text) return false;
  if (text.startsWith('#!q3n-format')) return true;
  return Q3N_START.test(text);
}

function exportJson(entries) {
  return JSON.stringify(entries.map(e => e.toDict()), null, 2);
}

function exportMarkdown(entries) {
  const lines = ['# Q3N Collection\n'];
  entries.forEach((e, i) => {
    lines.push(`## Entry ${i + 1}`);
    if (e.tag) lines.push(`**Tag:** ${e.tag}`);
    lines.push(`**Source:** [${e.uri}](${e.uri})`);
    lines.push('');
    e.quote.split('\n').forEach(p => {
      lines.push(p.trim() ? `> ${p}` : '>');
    });
    lines.push('');
    lines.push('---');
    lines.push('');
  });
  return lines.join('\n');
}

function exportFortune(entries) {
  return entries.map(e => e.quote + '\n%').join('\n');
}

function displayFortune(entries, options = {}) {
  if (!entries.length) return 'No fortunes found!';
  const entry = entries[Math.floor(Math.random() * entries.length)];
  const art = ASCII_ARTS[options.art] || ASCII_ARTS[Object.keys(ASCII_ARTS)[Math.floor(Math.random() * Object.keys(ASCII_ARTS).length)]];
  const lines = entry.quote.split('\n');
  const width = Math.min(Math.max(...lines.map(l => l.length), 0), 60);
  const box = ['+' + '-'.repeat(width + 2) + '+'];
  lines.forEach(l => { box.push('| ' + l.padEnd(width) + ' |'); });
  box.push('+' + '-'.repeat(width + 2) + '+');
  const result = options.noArt ? '' : (art + '\n');
  return result + box.join('\n') + '\n' + entry.attribution();
}

const ASCII_ARTS = {
  cookie: [
    '    .-~~~-.',
    '   /       \\',
    '  |  FORTUNE |',
    '   \\       /',
    '    `-...-\'',
  ].join('\n'),
  penguin: [
    '   .-.',
    '  (o o)',
    '  (   )',
    '  -"-"-',
  ].join('\n'),
  book: [
    '    .--.',
    '   |o_o |',
    '   |:_/ |',
    '  //   \\ \\',
    ' (|     | )',
    "/'\\_   _/`\\",
    '\\___)=(___/',
  ].join('\n'),
  cat: [
    ' /\\_/\\',
    '( o.o )',
    ' > ^ <',
  ].join('\n'),
  star: [
    '      .',
    '     /|\\',
    '    /*|*\\',
    '   /__|__\\',
    '  /__|*|__\\',
    '     |*|',
    '     |_|',
  ].join('\n'),
};

// ── CLI entry point ───────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === '--help' || command === '-h') {
    console.log('Q3N Parser — JavaScript implementation');
    console.log('');
    console.log('Usage:');
    console.log('  node q3n-parser.js extract <file>   Extract and display entries');
    console.log('  node q3n-parser.js validate <file>  Validate Q3N syntax');
    console.log('  node q3n-parser.js json <file>      Output as JSON');
    console.log('  node q3n-parser.js fortune <file>   Display random fortune');
    console.log('  node q3n-parser.js --help            Show this help');
    return;
  }

  const fs = require('fs');
  let content;
  const filePath = args[1];
  if (filePath) {
    try { content = fs.readFileSync(filePath, 'utf-8'); }
    catch (e) { console.error(`Error: Cannot read '${filePath}'`); process.exit(1); }
  } else {
    content = fs.readFileSync(0, 'utf-8');
  }

  const entries = parse(content);

  switch (command) {
    case 'extract':
      entries.forEach((e, i) => {
        console.log(`--- Entry ${i + 1} ---`);
        console.log(`URI:   ${e.uri}`);
        console.log(`Tag:   ${e.tag || '(none)'}`);
        const preview = e.quote.length > 60 ? e.quote.slice(0, 57) + '...' : e.quote;
        console.log(`Quote: ${preview}`);
        console.log(e.attribution());
        console.log();
      });
      if (!entries.length) console.log('No Q3N entries found.');
      break;

    case 'validate':
      if (entries.length) {
        console.log(`✓ Valid Q3N: ${entries.length} entry(ies) found`);
        process.exit(0);
      } else {
        console.log('✗ No valid Q3N entries found');
        process.exit(1);
      }
      break;

    case 'json':
      console.log(exportJson(entries));
      break;

    case 'fortune':
      console.log(displayFortune(entries, { noArt: args.includes('--no-art') }));
      break;

    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }
}

// ── Exports ────────────────────────────────────────────────────────────

const Q3NParser = {
  parse,
  serialize,
  detect,
  detectContent,
  detectContentType,
  Q3NEntry,
  URI_PARSERS,
  exportJson,
  exportMarkdown,
  exportFortune,
  displayFortune,
  SCHEME_CATEGORIES,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = Q3NParser;
  if (require.main === module) main();
} else if (typeof window !== 'undefined') {
  window.Q3NParser = Q3NParser;
}
