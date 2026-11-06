# PR #14 visual integration and validation gate

This document extends the articulated-animation work into a complete visual-quality and runtime-validation pass. It is an implementation checklist, not a claim that the items are already complete.

## Current baseline and constraints

- The published GitHub Pages build was inspected at 220 organisms. It rendered without visible missing resources or runtime errors, but the organism presentation was abstract and the observed frame rate was approximately 13 FPS.
- That inspection was against the published build, not this PR branch. It does not validate the new animation code.
- The 80 five-view PNGs are supplied by the stacked PR #13 asset branch. The layered SVG atlas in this PR is editable rig reference artwork; it is not a substitute for production near/far cut-out PNGs.
- Keep the simulation authoritative. Rendering may consume habitat and behaviour state, but must not invent ecological outcomes.

## Workstream A: production creature artwork and layered sprites

- [x] Integrate the 16 species' five directional poses into the runtime manifest (80 generated directional PNG entries across 16 species and five views). CI manifest checks validate coverage; browser URL loading is covered by the new screenshot workflow.
- [ ] Replace procedural placeholder organism silhouettes wherever a production pose exists; retain a deliberate fallback only for species without authored artwork.
- [ ] Split each creature into body, far appendages, near appendages, and optional detail/overlay layers with explicit pivots and depth order.
- [x] Directional pose selection uses explicit simulation orientation; turning clips now take precedence over stale orientation fields, with a regression assertion.
- [ ] Validate clipping, anchor placement, source aspect ratio, transparency fringes, and near/far overlap at small and large render sizes.
- [ ] Add asset-manifest validation that fails CI for missing files, invalid dimensions, duplicate view keys, or incomplete species/view coverage.

**Acceptance:** all 16 species render from production artwork in front, front-three-quarter, side, rear-three-quarter, and rear views; no procedural body placeholder is used when the corresponding production asset is available.

## Workstream B: animation validation against live simulation

- [ ] Validate all five directional poses and transitions in the actual browser renderer, including mirrored travel and turning in both directions.
- [ ] Tune far/near appendage pivots and occlusion against the painted body artwork; remove visible joint markers from production presentation unless intentionally part of the art style.
- [ ] Inspect body-strip deformation for gaps, seams, texture tearing, and silhouette collapse across the full flex range; clamp or replace the approximation where it fails.
- [ ] Exercise authored turning, feeding, hunting/attack, dying/dead, idle, and swim clips using real simulation state transitions and elapsed-time fields.
- [ ] Confirm animation phase remains deterministic under pause, speed changes, low frame rate, and entity removal/reinsertion.
- [ ] Add browser-level fixtures for each behaviour and representative species families.

**Acceptance:** screenshots and browser assertions demonstrate stable silhouettes, correct layer order, and visible state-specific motion for representative species and all supported behaviour clips.

## Workstream C: rendering performance separated from simulation cost

- [ ] Instrument simulation stepping and rendering as separate measurements. Report mean, p95, and maximum frame costs over a fixed sampling window.
- [ ] Break rendering cost down into background/terrain, flora, creature body, appendage layers, overlays, and UI/canvas composition where the current architecture permits.
- [ ] Record organism count, visible organism count, sprite cache hit/miss/load/failure counts, draw calls, and active deformation count alongside timings.
- [ ] Benchmark repeatable populations at 50, 100, 220, and 400 organisms, with a fixed seed and camera.
- [ ] Compare deformation enabled/disabled and layered appendages enabled/disabled to isolate their marginal cost.
- [ ] Avoid per-organism timers, allocations, and unconditional high-resolution timing calls in the hot path. Instrumentation must be sampled or opt-in.
- [ ] Set explicit frame-time budgets and document the bottleneck before applying batching, culling, level-of-detail, or caching changes.

**Acceptance:** a reproducible report identifies simulation versus rendering cost at 220 organisms and establishes whether the 30 FPS target is limited by the renderer, simulation, browser/compositor, or a combination. Do not infer this from simulation-step time alone.

## Workstream D: biome differentiation

- [ ] Define a data-driven visual profile for each supported habitat: coral reef, open ocean, deep sea, seagrass bed, kelp forest, rocky seabed, sandy seabed, and hydrothermal vent.
- [ ] Give each profile distinct terrain silhouettes, substrate materials, water colour/lighting/attenuation, particulate density, and depth cues.
- [ ] Drive flora placement and density from habitat suitability and local environmental conditions. Use dense, spatially coherent hotspots rather than uniform decorative scatter.
- [ ] Make species composition and visible population density respond to the existing habitat/ecology state; avoid hard-coded decorative species that contradict the simulation.
- [ ] Add habitat-specific lighting and background layers while preserving readable creature contrast and the established side-view art direction.
- [ ] Validate transitions between habitats and ensure each profile remains legible at overview and close-up zoom.

**Acceptance:** all eight habitats are visually distinguishable in matched screenshots, with terrain, flora, lighting, water conditions, and species composition consistent with the active habitat data.

## Workstream E: visual regression and browser evidence

- [ ] Add a deterministic browser screenshot suite using a fixed seed, fixed simulation time or controlled stepping, and stable viewport dimensions.
- [ ] Capture all eight habitats at overview and close-up zoom.
- [ ] Capture low, nominal, and stress populations (50, 220, and 400 organisms where supported).
- [ ] Include directional-pose and behaviour fixtures for the animation workstream.
- [ ] Store baseline screenshots as CI artifacts; compare with a perceptual/pixel-diff threshold that tolerates known browser antialiasing noise but catches missing layers, blank canvases, and major layout drift.
- [ ] Record browser console errors, failed network requests, sprite load failures, FPS, and render timing with each run.
- [ ] Keep screenshot evidence from the PR preview distinct from screenshots of the published main branch.

**Acceptance:** CI produces a browsable screenshot matrix and machine-readable diagnostics for each scenario. A screenshot of the current published build is not accepted as evidence for PR #14.

## Integration order

1. Land and verify PR #13's binary sprite assets.
2. Integrate production body and directional assets; establish layered appendage cut-outs and pivots.
3. Tune animation clips against those actual assets in a PR preview.
4. Add separate renderer/simulation profiling and resolve measured bottlenecks.
5. Implement biome visual profiles and ecology-driven hotspot composition.
6. Add deterministic screenshot regression coverage and use it as the final visual acceptance gate.

## Status

The existing PR #14 contains the initial procedural articulation, six-strip body-flex approximation, directional view resolver, and authored behaviour cues. The published-site inspection is baseline-only. The five workstreams above remain validation/integration scope; none should be marked complete until its acceptance criteria are demonstrated against a PR #14 browser build with the production PNG assets present.


## Implementation update

The production turnaround pack is present on this branch: 80 transparent directional PNGs, 16 species × five views. The runtime manifest contains all 80 entries and the existing CI manifest assertions validate species/view coverage. The sprite runtime resolves these authored poses directly.

A turning-state precedence bug was fixed: an organism carrying a stale explicit `view: "side"` no longer remains stuck in the side pose throughout its turning clip. The turning clip now owns view selection until its transition completes, and `tests/sprite-view.test.js` covers this regression.

The dashboard now reports separate median biome-render time and organism-list preparation time alongside total client draw median/P95 and frame-interval P95. The organism metric is intentionally labelled preparation, not sprite draw time; it must not be misrepresented as a complete per-organism render measurement.

A Playwright workflow now captures 24 screenshots across eight supported habitats and three zoom settings, and uploads console/network diagnostics as an artifact. It currently exercises the deterministic 220-organism local preview. Variable population fixtures, controlled simulation-time freezing, pixel-diff thresholds, and production browser screenshots with the real layered cut-out artwork remain incomplete.

**Layering limitation:** directional body poses are production PNGs. The independently animated far/near appendage silhouettes still use procedural vector geometry guided by the editable SVG pivot atlas. They are not yet independently painted cut-out PNG layers. This is a deliberate, documented gap rather than a claim that the generated body poses magically contain a complete skeletal rig.
