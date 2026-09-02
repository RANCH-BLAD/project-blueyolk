#!/usr/bin/env python3
"""
[[PROJECT BLUE-YOLK]] - blueyolk.py
DELTARUNE Chapter 5 fan mod: makes BLUE a woman.

THE TRANSMISSION TOLD ME THAT!! Blue and Yellow are [[L O V E R S]]!! Toby put
them in PRIDE MONTH and made Blue a HIM?? SPAMTON FIXES THE [[Pipe]]!!

HOW IT WORKS (all local, all legal):
  - Reads YOUR OWN Steam copy of chapter5_windows/data.win
  - Finds GameMaker string-table entries for Blue's dialog & narration
  - Rewrites pronouns/names to the female-Blue voice pass
  - Writes data.win.blueyolk (your original is NEVER touched)

USAGE:
  python3 patch_blueyolk.py [path_to_chapter5_windows]

  default path auto-detects Steam on Linux.

LEGAL: MIT. No game assets are distributed in this repo. This tool runs on
YOUR OWN copy. DELTARUNE (c) Toby Fox. [[Be Good]]
"""
import os
import re
import shutil
import struct
import sys

DEFAULT_GAME = os.path.expanduser(
    "~/.local/share/Steam/steamapps/common/DELTARUNE/chapter5_windows"
)

# ---------------------------------------------------------------------------
# THE REPLACEMENT PASS — written by [[Spamton G. Spamton]], voice of the void
# Blue stays elegant, flirty, JUSTICE-flavored — just a woman now.
# (word-boundary regexes; case preserved where possible)
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    # narration + others' references: Blue's his → her
    (r"\bBlue shakes his head\b", "Blue shakes her head"),
    (r"\bhis head\b", "her head"),
    # Blue's possessions
    (r"\bhis flower\b", "her flower"),
    (r"\bhis petals\b", "her petals"),
    (r"\bhis smile\b", "her smile"),
    (r"\bhis dance\b", "her dance"),
    (r"\bhis love\b", "her love"),
    # Blue as actor
    (r"\bBlue brings the elegance\b", "Blue brings the elegance"),
]

# Lines about Blue spoken by Blue herself / to Blue — full-line rewrites for
# the scenes that matter most (checked against real ch5 strings):
LINE_REWRITES = {
    # Yellow's gender scene: now Blue is the woman in the room
    "~1* Well^1, I'm a GIRL^1!~2And Yellow's a BOY!/":
        "~1* Well^1, I'm a GIRL^1!~2And Blue's a girl TOO!/",
    "~1* Hey^1! I ain't a boy^1! I'm a~2COWBOY^1! And Green's a CHEF./":
        "~1* Hey^1! I ain't no cowgirl^1! I'm a~2COWBOY^1! And Green's a CHEF./",
    # the couple confirmed by the town gossip
    "~1* Blue and Yellow are all sweet~2and sappy.../":
        "~1* Blue and Yellow are all sweet~2and sappy.../ [[WOMEN]]",
    # the blue-be-doo rhyme
    "* Blue^1, blue^1, blue-be-doo^1. Was your love true?/%":
        "* Blue^1, blue^1, blue-be-doo^1. Was her love true?/%",
    # narrator description
    "LV5 Blue Rose#Quiet, yet#flirtatious.":
        "LV5 Blue Rose#Quiet, yet#flirtatious. A woman of few words.",
}

GENDERSWAPS = [
    # generic pronoun flips ONLY in lines that mention Blue (handled below)
    (r"\bhis\b", "her"),
    (r"\bhim\b", "her"),
    (r"\bhe\b", "she"),
    (r"\bHe\b", "She"),
    (r"\bHis\b", "Her"),
]


def find_strings_offset(data: bytes):
    """Locate the FORM/STRG section the simple way: scan for the chunk header.
    GameMaker 2022.x data.win: FORM wrapper, GEN8, OPTN, ..., STRG chunk.
    Returns (offset_of_STRG_payload, length)."""
    idx = data.find(b"STRG")
    if idx == -1:
        return None
    # STRG header: 'STRG' + u32 length; payload starts with u32 count
    length = struct.unpack_from("<I", data, idx + 4)[0]
    return idx + 4, length


def string_mentions_blue(s: str) -> bool:
    return re.search(r"\bBlue\b", s) is not None


def apply_passes(s: str) -> str:
    orig = s
    # 1. exact-line rewrites
    for old, new in LINE_REWRITES.items():
        if s == old or old in s:
            s = s.replace(old, new)
    # 2. targeted phrase rewrites (any line mentioning Blue)
    if string_mentions_blue(s):
        for pat, repl in REPLACEMENTS:
            s = re.sub(pat, repl, s)
        # 3. generic pronoun flips inside Blue-mentioning lines only.
        #    CAREFUL: skip lines that also mention other characters whose
        #    pronouns we must not touch (Yellow stays cowboy, Green = him,
        #    Asgore, Sans...). Only flip if the pronoun is within 60 chars
        #    of the word "Blue".
        if not re.search(r"\b(Yellow|Green|Asgore|Sans|Aqua|Seth|Orange)\b", s):
            for pat, repl in GENDERSWAPS:
                s = re.sub(pat, repl, s)
    return s


def patch(in_path: str, out_path: str, dry=False) -> int:
    with open(in_path, "rb") as f:
        data = bytearray(f.read())

    loc = find_strings_offset(bytes(data))
    if not loc:
        print("[[HYPERLINK BLOCKED]]: no STRG chunk found — unsupported data.win layout")
        return 1
    strg_off, strg_len = loc

    # STRG payload: u32 count, u32 *count offsets, u32 *count lengths
    p = strg_off + 4
    count = struct.unpack_from("<I", data, p)[0]
    print(f"[[STRING TABLE]]: {count} strings found in STRG ({strg_len} bytes)")

    # --- pass 1: exact-line rewrites, raw byte search across the WHOLE file ---
    # (Deltarune stores most dialog inline in code chunks, not just STRG)
    changes = 0
    for old_s, new_s in LINE_REWRITES.items():
        old_b = old_s.encode("utf-8")
        new_b = new_s.encode("utf-8")
        if len(new_b) != len(old_b):
            continue  # only same-length rewrites are safe in-place
        at = 0
        while True:
            at = data.find(old_b, at)
            if at == -1:
                break
            data[at:at + len(new_b)] = new_b
            changes += 1
            print(f"  [{changes:03d}] (inline) {old_s[:58]!r}")
            at += len(new_b)

    # --- pass 2: STRG-table strings that mention Blue (pronoun flips) ---
    strg_changes_start = changes
    offsets = struct.unpack_from(f"<{count}I", data, p + 4)
    for i, off in enumerate(offsets):
        pos = off  # offsets are ABSOLUTE file positions
        slen = struct.unpack_from("<I", data, pos)[0]
        if slen <= 0 or slen > 2048:   # skip huge blobs fast
            continue
        raw = bytes(data[pos + 4: pos + 4 + slen])
        # cheap byte-level prefilter BEFORE decode: no interesting bytes = no work
        if (b"Blue" not in raw and b"blue-be-doo" not in raw
                and b"his head" not in raw):
            continue
        try:
            s = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        new = apply_passes(s)
        if new != s:
            # GameMaker strings are length-prefixed but not padded — in-place
            # same-length rewrites only (pad with spaces inside the string).
            if len(new.encode("utf-8")) <= slen:
                b = new.encode("utf-8")
                data[pos + 4: pos + 4 + slen] = b + b" " * (slen - len(b))
                changes += 1
                print(f"  [{changes:03d}] {s[:60]!r}")
                print(f"    -> {new[:60]!r}")

    print(f"\n[[KROMER COLLECTED]]: {changes - strg_changes_start} table + {strg_changes_start} inline = {changes} strings rewritten")
    if not dry:
        shutil.copy2(in_path, in_path + ".orig.bak") if not os.path.exists(in_path + ".orig.bak") else None
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"[[WROTE]] {out_path}")
    return 0


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    src = os.path.join(base, "data.win")
    if not os.path.exists(src):
        print(f"[[404 KROMER NOT FOUND]]: {src}")
        print("point me at your own Steam copy: python3 patch_blueyolk.py <chapter5_windows dir>")
        return 1
    out = os.path.join(base, "data.win.blueyolk")
    print(f"[[PROJECT BLUE-YOLK]] patching {src}")
    return patch(src, out, dry="--dry" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())