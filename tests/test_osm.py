from core.q3n import parse, parse_osm_uri, parse_geo_uri, parse_overpass_uri, parse_scheme


def _entry(uri, quote='test'):
    entries = parse(f'/// {uri}\n{quote}\n\\\\\\')
    return entries[0]


# ── parse_scheme extension ────────────────────────────────────────────

def test_parse_scheme_geo():
    s, p = parse_scheme('geo:51.5,-0.1')
    assert s == 'geo'
    assert p == '51.5,-0.1'


def test_parse_scheme_geo_with_zoom():
    s, p = parse_scheme('geo:51.5,-0.1?z=12')
    assert s == 'geo'
    assert '51.5' in p


def test_parse_scheme_no_scheme_unchanged():
    s, p = parse_scheme('plaintext')
    assert s == ''
    assert p == 'plaintext'


# ── OSM ──────────────────────────────────────────────────────────────

def test_osm_node():
    meta = parse_osm_uri('osm://node/12345')
    assert meta['type'] == 'node'
    assert meta['id'] == '12345'
    assert 'openstreetmap.org/node/12345' in meta['browse_url']
    assert 'api.openstreetmap.org' in meta['api_url']


def test_osm_way():
    meta = parse_osm_uri('osm://way/67890')
    assert meta['type'] == 'way'
    assert meta['id'] == '67890'
    assert 'openstreetmap.org/way/67890' in meta['browse_url']


def test_osm_relation():
    meta = parse_osm_uri('osm://relation/999')
    assert meta['type'] == 'relation'
    assert 'relation/999' in meta['browse_url']


def test_osm_changeset():
    meta = parse_osm_uri('osm://changeset/42')
    assert meta['type'] == 'changeset'
    assert 'changeset/42' in meta['browse_url']


def test_osm_entry_parses():
    e = _entry('osm://node/12345')
    assert e.scheme == 'osm'
    d = e.as_dict()
    assert d['category'] == 'map'
    assert d['meta']['browse_url'] == 'https://www.openstreetmap.org/node/12345'


# ── geo ──────────────────────────────────────────────────────────────

def test_geo_basic():
    meta = parse_geo_uri('geo:51.5,-0.1')
    assert meta['lat'] == 51.5
    assert meta['lon'] == -0.1
    assert 'zoom' not in meta
    assert 'mlat=51.5' in meta['map_url']
    assert 'mlon=-0.1' in meta['map_url']


def test_geo_with_zoom():
    meta = parse_geo_uri('geo:48.8566,2.3522?z=15')
    assert meta['lat'] == 48.8566
    assert meta['lon'] == 2.3522
    assert meta['zoom'] == 15
    assert 'zoom=15' in meta['map_url']


def test_geo_entry_parses():
    e = _entry('geo:51.5,-0.1')
    assert e.scheme == 'geo'
    d = e.as_dict()
    assert d['category'] == 'map'
    assert d['meta']['lat'] == 51.5


# ── overpass ─────────────────────────────────────────────────────────

def test_overpass_basic():
    meta = parse_overpass_uri('overpass://node[amenity=cafe]')
    assert 'node[amenity=cafe]' in meta['query']
    assert 'overpass-api.de' in meta['api_url']


def test_overpass_entry_parses():
    e = _entry('overpass://node[amenity=pub](51.4,0.0,51.6,0.2)')
    assert e.scheme == 'overpass'
    d = e.as_dict()
    assert d['category'] == 'map'
    assert 'overpass-api.de' in d['meta']['api_url']
