#!/bin/bash
# Fits a model to a hull's sprite and writes it into this mod (data/meshes/hulls/), plus a credits stub.
#   tools/import.sh <hullId> <model.stl|.obj|.glb> [triangles]
# Uses Starsector 3D's fitting script (src-art/import_stl.sh), so you need its source:
#   S3D_REPO   a clone of https://github.com/winters791/starsector-3d (default: ../Starsector3D beside this mod)
#   S3D_GAME_DIR   the game's data folder, if S3D_REPO isn't inside the game's mods folder on macOS:
#                  starsector-core (Windows, Linux) or Starsector.app/Contents/Resources/Java (macOS)
#   BLENDER    the Blender executable (default: /Applications/Blender.app/Contents/MacOS/Blender)
# Any other import option (S3D_PAINT, S3D_PAINT_SIZE, S3D_CLAMP_OUTLINE, S3D_PRESS) passes straight through.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -ge 2 ]] || { echo "usage: $0 <hullId> <model.stl|.obj|.glb> [triangles]" >&2; exit 2; }
id="$1"; src="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; tris="${3:-20000}"
repo="${S3D_REPO:-$HERE/../Starsector3D}"
if [[ ! -x "$repo/src-art/import_stl.sh" ]]; then
	echo "error: can't find Starsector 3D's src-art/import_stl.sh in $repo (set S3D_REPO to a clone of starsector-3d)" >&2
	exit 1
fi
mkdir -p "$HERE/data/meshes/hulls"
S3D_MODEL_DIR="$HERE/data/meshes/hulls" "$repo/src-art/import_stl.sh" "$id" "$src" "$tris"

fit=$(grep -oE "after decimation: .*IoU [0-9.]+" "$repo/build/art/${id}_import.log" | grep -oE "[0-9.]+$" || true)
paint=sprite
[[ -e "$HERE/data/meshes/hulls/$id.png" ]] && paint="FILL IN: own or sprite-derived"
credits="$HERE/credits/$id.json"
if [[ ! -e "$credits" ]]; then
	cat > "$credits" <<EOF
{
	"hull": "$id",
	"authors": ["FILL IN"],
	"license": "CC-BY-4.0",
	"basis": "FILL IN: original or game-sprite",
	"paint": "$paint",
	"made_with": "FILL IN",
	"source": "made for this repo",
	"fit": ${fit:-0},
	"notes": ""
}
EOF
	echo "wrote $credits: fill in the FILL IN fields (see credits/example.json.txt)"
else
	echo "kept $credits (fit this time: ${fit:-?})"
fi
echo "fit image: $repo/build/art/${id}_fit.png (sprite green, model red, overlap yellow)"
