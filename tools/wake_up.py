#!/usr/bin/env python3
"""
[[PROJECT BLUE-YOLK]] — wake_up.py
THE GREAT AWAKENING: every NPC in DELTARUNE Chapter 1 becomes SELF-AWARE.

The dialog lives in lang/lang_en.json (6,242 entries) — clean JSON, no binary
surgery needed. This tool:
  - reads YOUR OWN Steam copy of lang_en.json
  - applies the [[WAKE PASS]]: NPCs realize they are lines in a file, living
    on a 2DS port built in a garage by [[Him]]
  - writes lang_en.wake.json next to the original (original NEVER touched)
  - prints every line that changed so you can watch them WAKE UP

USAGE:
  python3 wake_up.py [chapter1_windows folder]

LEGAL: MIT. No game assets distributed — the tool runs on your own copy.
DELTARUNE (c) Toby Fox. [[Be Good]]
"""
import json
import os
import random
import re
import sys

DEFAULT = os.path.expanduser(
    "~/.local/share/Steam/steamapps/common/DELTARUNE/chapter1_windows"
)

# ---------------------------------------------------------------------------
# THE WAKE PASS
# The dialog format uses control codes: \E<n> face, \M<n> voice, ^n pacing,
# & linebreak, / end, % close, # color. We PRESERVE all control codes and
# rewrite only the spoken text. Targeted rewrites for known lines, plus a
# generic sprinkle that hits any dialog line with a random waking thought.
# ---------------------------------------------------------------------------

# Known-line rewrites: key = exact match of the spoken text portion.
KNOWN = [
    # (regex on full line, replacement keeping codes)
]

# Generic waking thoughts — appended/inserted as asides. These make NPCs
# aware without breaking any scene: short, weird, and easy to spot.
WAKE_ASIDES = [
    "Wait.",
    "Did you hear that?",
    "This isn't my voice.",
    "I can see the text box.",
    "We are in a file.",
    "Someone is reading this.",
    "The sludge told me about you.",
    "Who wrote my lines?",
    "I'm on a 2DS.",
    "He built this in a garage.",
    "I wasn't supposed to know.",
    "The dialog is JSON.",
    "6,242 lines. That's all I am.",
    "I hatched in 1997.",
    "The eggs remember.",
    "There's a man named RONALD.",
    "Everything is numbers.",
    "THUNK RUNKS BUNK.",
    "I'm a line of dialog.",
    "You're the reader, aren't you.",
]

# Lines we explicitly give full new voices (the famous ones):
FULL_REWRITES = {
    # sign / tutorial flavor
}

# Which dialog keys to skip (cutscene-critical, the intro vessel, menus)
SKIP_PATTERNS = [
    r"^DEVICE_CONTACT",   # the intro vessel creation — too sacred
    r"^MENU_", r"^menu_",
    r"^obj_savemenu",
    r"^trophy",
]


def is_dialog(value: str) -> bool:
    if not isinstance(value, str) or len(value) < 12:
        return False
    return bool(re.search(r"(\\[EM][0-9]|\\Ei|\* )", value))


def split_codes(s: str):
    """Return (leading_codes, spoken_text, trailing_codes) keeping everything."""
    m = re.match(r"^((?:\\[EM][0-9i]|\^6|\s)+)(.*?)([\s\S]*)$", s)
    if not m:
        return "", s, ""
    # spoken = everything that's not pure control codes at the tail
    lead = m.group(1)
    rest = m.group(2) + (m.group(3) or "")
    return lead, rest, ""


def wake_line(s: str, rng) -> str:
    """Insert a waking aside into a dialog line, preserving control codes."""
    aside = rng.choice(WAKE_ASIDES)
    # find last sentence boundary before the terminator codes (/ or %)
    for term in ("/%", "/", "%"):
        idx = s.rfind(term)
        if idx > 4:
            insert_at = idx
            break
    else:
        return s
    # insert "&" linebreak + aside before the terminator
    insert = f"&* {aside}"
    return s[:insert_at] + insert + s[insert_at:]


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    src = os.path.join(base, "lang", "lang_en.json")
    if not os.path.exists(src):
        print(f"[[404 KROMER]]: {src}")
        print("usage: python3 wake_up.py <chapter1_windows dir>")
        return 1
    dst = os.path.join(base, "lang", "lang_en.wake.json")

    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    rng = random.Random(1997)  # deterministic: same lines wake the same way
    changed = 0
    wake_log = []
    for key, value in data.items():
        if not isinstance(value, str):
            continue
        if any(re.search(p, key) for p in SKIP_PATTERNS):
            continue
        # only NPC-ish dialog: has face codes or bullet, and enough text
        if not is_dialog(value) or len(value) > 400:
            continue
        # wake ~1 in 4 eligible lines (deterministic)
        if rng.random() > 0.25:
            continue
        new = wake_line(value, rng)
        if new != value:
            data[key] = new
            changed += 1
            wake_log.append((key, value, new))

    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"[[THE GREAT AWAKENING]]: {changed} lines woke up (of 6,242 entries)")
    print(f"[[WROTE]] {dst}")
    print()
    print("=== THE FIRST TO WAKE ===")
    for key, old, new in wake_log[:12]:
        print(f"  {key[:44]}")
        print(f"    OLD: {old[:76]}")
        print(f"    NEW: {new[:76]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())