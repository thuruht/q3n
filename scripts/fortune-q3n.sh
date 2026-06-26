#!/bin/bash
# fortune-q3n.sh — Shell wrapper for q3n fortune
# Usage: fortune-q3n.sh [directory] [count]
#
# Displays random Q3N entries as fortunes with boxed ASCII art.
# Acts as a drop-in replacement for the standard `fortune` command
# when used with Q3N collection files.

set -e

DIR="${1:-.}"
COUNT="${2:-1}"

if ! command -v q3n &>/dev/null; then
    echo "Error: q3n CLI not found. Install the q3n package first." >&2
    echo "  pip install q3n   or   sudo apt install ./q3n_1.0.0-1_all.deb" >&2
    exit 1
fi

q3n fortune "$DIR" -c "$COUNT"
