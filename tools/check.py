#!/usr/bin/env python3
"""Checks every model in data/meshes/hulls against the contribution rules, without the game or Blender.

  python3 tools/check.py                 check everything (CI runs this)
  python3 tools/check.py --write-credits also regenerate CREDITS.md from credits/*.json

Checked: each .obj has the Starsector 3D header and at most MAX_TRIS triangles; each model has a complete
credits/<hullId>.json with an accepted license; a .png sits beside the .obj exactly when the credits say the
model has its own paint, and is a real PNG no bigger than MAX_PAINT; CREDITS.md is up to date.
The fit to the sprite and the per-class triangle budget need the game, so reviewers check those.
"""

import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HULLS = os.path.join(ROOT, "data", "meshes", "hulls")
CREDITS = os.path.join(ROOT, "credits")
CREDITS_MD = os.path.join(ROOT, "CREDITS.md")

MAX_TRIS = 80000          # capitals; smaller classes have lower budgets (see CONTRIBUTING.md)
MAX_OBJ_BYTES = 20 << 20
MAX_PAINT = 4096          # pixels per side
MAX_PNG_BYTES = 25 << 20
LICENSES = {"CC-BY-4.0", "CC0-1.0"}
BASES = {"original", "game-sprite"}
PAINTS = {"sprite", "own", "sprite-derived"}
FIELDS = ["hull", "authors", "license", "basis", "paint", "made_with", "source", "fit", "notes"]


def check_obj(path, errors):
    name = os.path.basename(path)
    if os.path.getsize(path) > MAX_OBJ_BYTES:
        errors.append("%s: bigger than %d MB" % (name, MAX_OBJ_BYTES >> 20))
    header = False
    tris = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i < 10 and line.startswith("# s3d sprite "):
                header = True
            if line.startswith("f "):
                tris += max(0, len(line.split()) - 3)
    if not header:
        errors.append("%s: no '# s3d sprite <w> <h>' header (make it with tools/import.sh)" % name)
    if tris == 0:
        errors.append("%s: no faces" % name)
    if tris > MAX_TRIS:
        errors.append("%s: %d triangles, more than %d" % (name, tris, MAX_TRIS))
    return tris


def check_png(path, errors):
    name = os.path.basename(path)
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        errors.append("%s: not a PNG file" % name)
        return
    w, h = struct.unpack(">II", head[16:24])
    if w > MAX_PAINT or h > MAX_PAINT:
        errors.append("%s: %dx%d, bigger than %d px a side" % (name, w, h, MAX_PAINT))
    if os.path.getsize(path) > MAX_PNG_BYTES:
        errors.append("%s: bigger than %d MB" % (name, MAX_PNG_BYTES >> 20))


def check_credits(hull, has_png, errors):
    path = os.path.join(CREDITS, hull + ".json")
    if not os.path.isfile(path):
        errors.append("%s: credits/%s.json is missing (see credits/example.json.txt)" % (hull, hull))
        return None
    try:
        c = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        errors.append("credits/%s.json: not valid JSON (%s)" % (hull, e))
        return None
    for k in FIELDS:
        if k not in c:
            errors.append("credits/%s.json: missing \"%s\"" % (hull, k))
    if "FILL IN" in json.dumps(c):
        errors.append("credits/%s.json: still has FILL IN fields" % hull)
    if c.get("hull") != hull:
        errors.append("credits/%s.json: \"hull\" is %r, should be %r" % (hull, c.get("hull"), hull))
    if not isinstance(c.get("authors"), list) or not c.get("authors") or not all(isinstance(a, str) and a.strip() for a in c["authors"]):
        errors.append("credits/%s.json: \"authors\" must be a list of names" % hull)
    if c.get("license") not in LICENSES:
        errors.append("credits/%s.json: license %r is not one of %s" % (hull, c.get("license"), ", ".join(sorted(LICENSES))))
    if c.get("basis") not in BASES:
        errors.append("credits/%s.json: basis %r is not one of %s" % (hull, c.get("basis"), ", ".join(sorted(BASES))))
    paint = c.get("paint")
    if paint not in PAINTS:
        errors.append("credits/%s.json: paint %r is not one of %s" % (hull, paint, ", ".join(sorted(PAINTS))))
    elif has_png and paint == "sprite":
        errors.append("%s: has %s.png but credits say paint \"sprite\" (own or sprite-derived?)" % (hull, hull))
    elif not has_png and paint != "sprite":
        errors.append("%s: credits say paint %r but there is no %s.png" % (hull, paint, hull))
    if not isinstance(c.get("fit"), (int, float)) or not 0 <= c.get("fit", -1) <= 1:
        errors.append("credits/%s.json: \"fit\" must be the 0..1 number tools/import.sh printed" % hull)
    return c


def credits_md(entries):
    lines = ["# Credits", "",
             "Generated from credits/*.json by `python3 tools/check.py --write-credits`; don't edit by hand.", "",
             "| Hull | Authors | License | Based on | Paint | Made with | Triangles | Fit |",
             "|---|---|---|---|---|---|---|---|"]
    paint_label = {"sprite": "game sprite (at runtime)", "own": "own texture", "sprite-derived": "texture from the game's sprite*"}
    basis_label = {"original": "original", "game-sprite": "the game's sprite"}
    for hull, c, tris in sorted(entries, key=lambda e: e[0]):
        src = c.get("source", "")
        made = c.get("made_with", "") + ((" ([source](%s))" % src) if src.startswith("http") else "")
        lines.append("| %s | %s | %s | %s | %s | %s | %d | %.2f |" % (
            hull, ", ".join(c.get("authors", [])), c.get("license", ""), basis_label.get(c.get("basis"), "?"),
            paint_label.get(c.get("paint"), "?"), made, tris, c.get("fit", 0)))
    lines += ["", "\\* Textures made from Starsector's own ship art: not covered by this repo's open license, "
              "included only for use with the game (see LICENSE).", ""]
    return "\n".join(lines)


def main():
    write = "--write-credits" in sys.argv[1:]
    errors = []
    entries = []
    files = sorted(os.listdir(HULLS)) if os.path.isdir(HULLS) else []
    for f in files:
        if f.startswith(".") or f == ".gitkeep":
            continue
        stem, ext = os.path.splitext(f)
        if ext == ".png":
            if not os.path.isfile(os.path.join(HULLS, stem + ".obj")):
                errors.append("%s: no %s.obj beside it" % (f, stem))
            else:
                check_png(os.path.join(HULLS, f), errors)
        elif ext != ".obj":
            errors.append("data/meshes/hulls/%s: only <hullId>.obj and <hullId>.png belong here" % f)
    for f in files:
        stem, ext = os.path.splitext(f)
        if ext != ".obj":
            continue
        tris = check_obj(os.path.join(HULLS, f), errors)
        c = check_credits(stem, os.path.isfile(os.path.join(HULLS, stem + ".png")), errors)
        if c is not None:
            entries.append((stem, c, tris))
    hulls = {os.path.splitext(f)[0] for f in files if f.endswith(".obj")}
    for f in sorted(os.listdir(CREDITS)):
        if f.endswith(".json") and f[:-5] not in hulls:
            errors.append("credits/%s: no data/meshes/hulls/%s.obj" % (f, f[:-5]))

    md = credits_md(entries)
    if write:
        with open(CREDITS_MD, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("wrote CREDITS.md (%d models)" % len(entries))
    elif not os.path.isfile(CREDITS_MD) or open(CREDITS_MD, encoding="utf-8").read() != md:
        errors.append("CREDITS.md is out of date: run python3 tools/check.py --write-credits")

    for e in errors:
        print("error: " + e)
    print("%d model(s), %d problem(s)" % (len(hulls), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
