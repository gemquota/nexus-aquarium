# PR #14 visual integration and regression gate

This document records the implementation and the evidence required to accept the five visual-quality workstreams. It distinguishes code that is implemented from checks that still need a passing browser run.

## A. Production artwork and layered rendering

- [x] Integrate 80 transparent generated turnaround PNGs: 16 species × five views.
- [x] Runtime manifest maps every species/view pair to its own production pose.
- [x] Sprite CI checks every generated file exists, has a valid PNG signature, has non-zero dimensions and includes an alpha channel; it also checks the complete, duplicate-free 16 × 5 matrix.
- [x] Render far appendages behind the production body pose and near appendages in front, using the editable pivot atlas and species rig profiles.
- [x] Keep a fallback renderer for species without an authored production pose.
- [ ] Replace procedural vector appendage shapes with individually painted, transparent cut-out assets. The current body poses are production PNGs, while near/far appendages are articulated vector geometry. This limitation is explicit and must not be described as fully painted cut-out artwork.

## B. Animation and live-state behaviour

- [x] Species-specific locomotion profiles and deterministic phase for all 16 turnaround species.
- [x] Proximal/distal articulation for fins and flippers, plus jellyfish bell/tentacle motion.
- [x] Authored turning, feeding, hunting, dying, idle and swim states consume organism behaviour and elapsed-time fields.
- [x] Turning state takes precedence over stale explicit orientation; unit regression covers the transition.
- [x] Browser fixtures exercise all six behaviour states with the complete 16-species set.
- [ ] Inspect and tune all silhouettes, joints, mirrored poses and body-strip seams in a live browser session. The automated browser suite is evidence collection, not a substitute for human visual review of its artifacts.

## C. Rendering and simulation performance

- [x] Keep simulation-step telemetry separate from browser draw measurements.
- [x] Measure total draw, frame interval, biome draw, organism-list preparation and organism draw separately.
- [x] Sample far-appendage, production-body and near-appendage rendering independently for one in eight organisms, avoiding a high-resolution timer call for every organism.
- [x] Expose median/P95 samples for the three sprite layers in the performance panel.
- [x] Browser fixture matrix covers 50, 220 and 400 organisms and writes population-specific render measurements to report.json.
- [ ] Run and inspect the benchmark artifact before making a performance claim. The matrix measures the local browser preview; backend simulation step cost remains a separate engine metric. No claim is made that the previous 13 FPS observation has been resolved.

## D. Habitat differentiation

- [x] Retain data-driven biome profiles for coral reef, open ocean, deep sea, seagrass, kelp forest, rocky seabed, sandy seabed and hydrothermal vent.
- [x] Apply habitat-specific water palettes and distinct substrate, flora density, growth forms and hotspot clustering.
- [x] Preserve day-phase and weather input to surface and water presentation.
- [x] Browser matrix captures every supported habitat at overview, home and close zoom, across all three population fixtures.
- [ ] Review the resulting screenshot matrix for contrast, ecological plausibility and visual distinction. Species composition remains driven by simulation state rather than being fabricated by the renderer.

## E. Visual regression and browser evidence

- [x] Deterministic local preview fixtures use a fixed seed, frozen simulation clock and explicit 50/220/400 population controls.
- [x] Capture 8 habitats × 3 zoom states × 3 populations (72 screenshots).
- [x] Capture six behaviour states with all 16 species (6 additional screenshots).
- [x] Repeat each habitat/population/zoom capture and compare decoded pixels, failing if more than 0.1% differ.
- [x] Record console errors, failed network requests, sprite-load failures and population-specific renderer/layer timings.
- [x] Upload screenshots and report.json as a CI artifact from the primary pull-request workflow.
- [ ] Inspect the first successful PR artifact and establish long-lived visual baselines. Current pixel comparison verifies deterministic repeat captures within one run; it is not yet a cross-commit golden-image baseline.

## CI status and known boundaries

The pull-request workflow runs backend tests, JavaScript syntax checks, sprite/manifest validation and the browser screenshot matrix. A run is only accepted when those checks finish green and the report artifact contains all 78 expected captures.

The renderer is layered, but the appendage artwork is still vector-generated rather than separately painted cut-out PNGs. The browser matrix is deterministic and broad, but cross-commit golden-image baselines and a human review of the resulting screenshots remain separate acceptance steps. Performance numbers must be read from the CI report rather than inferred from the test configuration.

## Implementation notes

- Visual fixtures are opt-in through `?visual-regression=1&freeze=1&population=220`; normal simulation behaviour is unchanged.
- The preview test API is exposed only as a browser fixture helper. It does not change backend simulation state.
- The performance display labels organism preparation separately from organism drawing and samples individual sprite layers at 1:8.
- The browser test uses the same dashboard and runtime asset manifest as the normal app.
