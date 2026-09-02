#!/usr/bin/env python3
"""[[TEST]] validates dialog JSON structure for project-blueyolk mod passes."""
import json, sys

def main(path):
    with open(path) as f:
        data = json.load(f)
    assert "speaker" in data, "missing speaker"
    assert isinstance(data.get("lines"), list), "missing lines"
    for i, line in enumerate(data["lines"]):
        assert "id" in line, f"line {i}: missing id"
        assert "text" in line, f"line {i}: missing text"
    print(f"OK: {len(data['lines'])} lines validated for speaker '{data['speaker']}'")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mod/dialog/blue_dialog_test.json")
