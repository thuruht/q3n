import csv
import io


def export_anki_csv(entries):
    """Export entries as Anki-compatible CSV (Quote, Source, Tag, URI)."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Quote', 'Source', 'Tag', 'URI'])
    for e in entries:
        quote = e.quote.replace('\n', ' ').replace('\r', '')
        source = e.attribution()
        tag = e.tag or ''
        writer.writerow([quote, source, tag, e.uri])
    return out.getvalue()
