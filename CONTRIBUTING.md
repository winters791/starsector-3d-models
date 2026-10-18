# Contributing a ship model

Thanks for helping! A contribution is one hull's model, fitted to that hull's sprite, plus a credits file.

## What you need

- Starsector with [Starsector 3D](https://github.com/winters791/starsector-3d) installed, and a clone of the
  Starsector 3D repository (the fitting script lives in its `src-art/` folder and reads the hull's sprite from
  your game).
- [Blender](https://www.blender.org/) 4.2 or newer.
- Your model as `.stl`, `.obj` (with `.mtl` + image for a textured one) or `.glb`.

Tell the script where things are with environment variables (bash; on Windows use Git Bash or WSL):

| variable | what | default |
|---|---|---|
| `S3D_REPO` | your clone of starsector-3d | `../Starsector3D` beside this mod |
| `S3D_GAME_DIR` | the game's data folder: `starsector-core` (Windows, Linux) or `Starsector.app/Contents/Resources/Java` (macOS) | found when the clone sits in the game's `mods` folder on macOS |
| `BLENDER` | the Blender program | `/Applications/Blender.app/Contents/MacOS/Blender` |

## Rules

1. **You must have the right to share it.** Make it yourself, or use a model whose license allows
   redistribution and modification (CC0, CC BY, ...), and say so in the credits. Not accepted: models ripped
   from other games or films, store assets that forbid redistribution, anything you're unsure about.
   AI tools: check that the tool's terms let you publish its output under CC BY.
2. **Say what it's based on.** If you made it from the game's sprite (for example image-to-3D from the
   sprite), set `"basis": "game-sprite"`. A paint texture made from the sprite is `"paint": "sprite-derived"`:
   it stays the game's art and isn't covered by this repo's open license.
3. **Match the sprite from above.** Starsector 3D lines the model up with the sprite's outline; weapons,
   engines and shields sit where the sprite says. Aim for a fit of 0.85 or better (the script prints it).
4. **No modelled guns.** The game draws each ship's actual weapons on its slots. Leave mounts empty or flat
   (`S3D_PRESS` in the fitting script can press modelled turrets flat; see `src-art/import_stl.py`).
5. **Triangle budget:** at most 80,000 for capitals, 40,000 cruisers, 20,000 destroyers, 10,000 frigates.
6. One hull per pull request. A better model for a hull that already has one is welcome; say why in the PR.

## Steps

1. Fit your model to the hull:

   ```bash
   tools/import.sh <hullId> /path/to/model.glb 80000
   ```

   This writes `data/meshes/hulls/<hullId>.obj` (and `<hullId>.png` for a textured model), a fit image
   `<S3D_REPO>/build/art/<hullId>_fit.png` (sprite green, model red, overlap yellow) and a credits stub.
   Hull IDs are the `.ship` file names in `starsector-core/data/hulls/` (e.g. `onslaught`, `atlas2`).

2. Look at it in a battle: put this mod in Starsector's `mods` folder, enable it, and fight with that ship
   (the refit screen's simulator is quickest). Press K in a battle to reload after changing a file.

3. Fill in `credits/<hullId>.json` (see `credits/example.json.txt`) and run `python3 tools/check.py`.

4. Open a pull request with the `.obj`, the `.png` if any, and the credits file. Attach the fit image and a
   screenshot. CI runs `tools/check.py`; a maintainer checks the fit and looks in game before merging.
