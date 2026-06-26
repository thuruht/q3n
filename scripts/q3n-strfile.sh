#!/bin/bash
# q3n-strfile.sh — Generate strfile-indexed fortune files from Q3N collections
# Usage: q3n-strfile.sh <input.q3n> [output.dat]
#
# Converts a Q3N file to strfile(8)-compatible fortune format and indexes it
# for use with the standard `fortune` command.
#
# Requires: q3n CLI, strfile (from bsdmainutils / freebsd-glue)

set -e

INPUT="${1:?Usage: q3n-strfile.sh <input.q3n> [output]}" 
OUTPUT="${2:-$(basename "$INPUT" .q3n).dat}"

TMPFILE=$(mktemp /tmp/q3n-fortune-XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

q3n export "$INPUT" -o "$TMPFILE" -f fortune 2>/dev/null || \
    python3 -c "
import sys; sys.path.insert(0, '.')
from core.q3n import parse_file
from core.fortune import export_fortune
entries = parse_file('$INPUT')
with open('$TMPFILE', 'w') as f:
    f.write(export_fortune(entries))
"

if [ ! -s "$TMPFILE" ]; then
    echo "Error: no entries found in $INPUT" >&2
    exit 1
fi

if ! command -v strfile &>/dev/null; then
    echo "Warning: strfile not found. Install bsdmainutils or freebsd-glue." >&2
    echo "Writing raw fortune file to: $TMPFILE" >&2
    cp "$TMPFILE" "$OUTPUT"
    exit 0
fi

strfile "$TMPFILE" "$OUTPUT"
echo "Created: $OUTPUT"
