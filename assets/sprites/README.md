# Nexus Aquarium — side-view sprite sources

The aquarium is a **horizontal side-view ocean cross-section**. Do not import top-down tiles or sprites into the main scene.

## Status

This commit adds the vetted source catalogue and safe local import tooling. It does **not** contain third-party sprite binaries yet. The repository is public, and several packs explicitly prohibit redistribution of their raw PNGs/ZIPs. Those purchased packs must be imported from the owner's own downloads into a local/private asset directory; do not commit those raw files to this public repository.

## Recommended visual stack

1. **Fathom** — best cohesive underwater core: 33 animated side-on creatures, 35 props, 65 tiles, four seamless parallax backgrounds, effects, and a shared 53-colour palette. The free sampler has four animated creatures; the full pack is paid.
2. **Kenney Fish Pack** — CC0 supplementary fish and marine sprites; listed in OpenGameArt's side-scroll collection.
3. **Bubbabba Tropical Island** — side-view island, beach, palm trees, reef terrain, kelp, animated macaw and crab.
4. **Elthen Seagull** — dedicated idle/flap/glide seabird.
5. **Fleuff Underwater Props** — animated kelp, seaweed, coral, clams, shipwreck props and bubbles; pair with its own tileset if that terrain is wanted.
6. **Sunken City** and **SakPix Aquatic World** — optional additional biome/architecture sets. SakPix has an 80-asset free demo but a noticeably chunkier style.

The exact pack contents, source links, prices observed, licences, projection and acquisition state are in [sources.json](./sources.json).

## Packs deliberately not selected for the main scene

- Polyy 2D Fish: attractive 30-angle sprites rendered at 25° elevation, but not a flat side profile.
- Cozy Fishing and Beach & Island Top-Down Props: top-down projection.
- Underwater Reef Pack: mixed assets; projection/style needs per-image verification.

These can remain alternate-view references, not default scene assets.

## Importing purchased or downloaded packs

1. Download the pack from its creator's page and read the licence included in the ZIP.
2. Put the ZIP in `asset_staging/` (this folder is intentionally ignored by Git).
3. Run:

   ```sh
   python3 tools/import_sprite_packs.py asset_staging/fathom-underwater.zip --pack fathom-underwater
   ```

4. The importer extracts safe image/metadata files to `local_assets/sprites/<pack-id>/` and writes a local manifest. It rejects path traversal, symlinks, oversized entries and unsupported files.
5. Keep paid/non-redistributable assets out of Git. For public deployment, use only CC0 assets or a hosting arrangement that complies with the creator's licence.

The importer only stages files; it does not auto-publish them or alter the simulation's species catalogue.

## Renderer integration contract

- Keep source pixels crisp (`imageSmoothingEnabled = false` for pixel art passes).
- Preserve each asset's native aspect ratio and frame dimensions.
- Use horizontal flip for left-facing creatures when the source faces right.
- Keep parallax/island silhouettes behind the water surface; draw birds in the sky layer.
- Anchor plants at their roots and seabed props at their base.
- Use each pack's own palette/style as a separate biome where styles differ.
- Never infer a species from a generic bird/fish sprite; record generic fallbacks as generic.

## Licence discipline

The project repository is public. Only commit asset files whose licence permits redistribution in a public repository (for example, CC0). A licence allowing use in a commercial game does not automatically allow publishing the raw asset files in a public source repository.
## Sprite renderer integration

The browser now loads `sprite-runtime.js` before the aquarium renderer. It reads `runtime-manifest.json` and can draw imported side-view creature, plant, seabird and island sprites. If an image is absent or fails to load, the existing procedural renderer remains the fallback. The simulation and its data model are unchanged.

### Importing the free Kenney fish pack

Open [Kenney's Fish Pack on OpenGameArt](https://opengameart.org/node/79308), download `kenney_fish-pack_2.0.zip`, and place it in `asset_staging/`. It is listed as CC0 and in the site's side-scroll sprite collection. Then run:

```sh
python3 tools/import_sprite_packs.py asset_staging/kenney_fish-pack_2.0.zip --pack kenney-fish --public
```

This writes the extracted CC0 image files to `assets/sprites/imported/kenney-fish/` and updates `runtime-manifest.json`. Review the generated import manifest, then commit the imported files and manifest. The importer deliberately skips unparsed atlas/spritesheet images to avoid stretching an entire sheet as one fish. Individual PNGs are used as static sprites until frame metadata is available.

For paid packs, omit `--public`; the files remain in the ignored `local_assets/` folder and must not be pushed to the public repository. Private licensed packs are not yet wired into public GitHub Pages hosting.


## Production flora sprites

The side-view habitat renderer uses the transparent Kenney seaweed PNG variants by growth form: green seaweed for kelp forests, grass variants for seagrass beds, and background seaweed variants for mangrove/estuary dressing. Five original, transparent SVG sprites are included for coral reefs: staghorn coral, brain coral, fan coral, tube sponges and anemones. These are registered in `runtime-manifest.json` and anchored to the seabed by the sprite runtime. Procedural vegetation is retained only as a load-failure fallback, not as the normal rendered plant layer.


## Unified sprite standard

The active runtime manifest now uses the NEXUS outlined, cel-shaded style for coral, giant kelp, seagrass, mangrove roots, seabed rocks, sand/dirt surface tiles, bubbles and seabirds. The older Kenney generic fish, seaweed, rocks, terrain props and the earlier bird are no longer registered as runtime assets. The Kenney source files remain in the repository for provenance/reference, but are not drawn by the live renderer.

Creature rendering uses the 16 species-specific five-view production sets. Species without their own production artwork resolve to a deliberate closest-family fallback among those 16 standard-style species; the old Kenney generic fish are not used as visual fallbacks. Exact species art always takes priority.
