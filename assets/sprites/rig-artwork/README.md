# Articulated creature animation

PR #14 now separates the creature into three render passes:

1. **Far-side appendages**: reduced-opacity flippers/fins behind the body.
2. **Body**: the painted directional turnaround, segmented into six overlapping horizontal strips when spine flex is active.
3. **Near-side appendages**: foreground flippers/fins, joints and behaviour cues.

The source artwork atlas is `appendage-layer-atlas.svg`. It contains 16 species symbols, each with independent `<species>-far` and `<species>-near` groups and body-relative pivot metadata. It is intended as editable layered source artwork. The live canvas renderer uses corresponding procedural vector paths so pivots can be animated from simulation state without loading and re-rasterising SVG for every organism.

## Articulation and deformation

- Each appendage is attached at a body-relative pivot.
- Flippers/fins use a proximal hinge, distal bend cue and visible joint marks.
- Near/far layers are drawn separately around the body sprite.
- The body uses six overlapping source-image strips with a travelling vertical offset and local rotation. This is a lightweight 2D spine mesh approximation, not a full deformable mesh solver.
- Jellyfish use a bell contraction cycle and independently phased tentacles.
- Tail stroke, fin stroke and body flex scale with swim speed while stable organism IDs preserve deterministic phase.

## Authored behaviour clips

The renderer reads these optional organism fields:

- `animation_state` (preferred), or `behaviour`, `behavior`, or `state`
- `animation_elapsed` (preferred elapsed seconds), or `state_elapsed` / `behaviour_elapsed`
- `animation_started_at` (simulation-time start, used when elapsed is not supplied)
- `turn_target_view` or `target_view` for turning clips

Supported states:

| State | Motion |
| --- | --- |
| `turning` | Side → three-quarter → requested front/rear pose; body pitch and travelling spine flex |
| `feeding` | Head/jaw opening cue, reduced thrust, controlled fin movement |
| `hunting` / `attack` | Short lunge, stronger tail stroke and jaw cue |
| `dying` / `dead` | Progressive roll, reduced body scale/opacity and sinking |
| `idle` | Low-amplitude species cycle |
| `swim` | Species-specific locomotion cycle |

The simulation remains authoritative: this renderer does not invent predator/prey decisions or change organism state. It only visualises state supplied by the engine. When no behaviour state is supplied, it uses the normal swim cycle.

## Browser review and visual tuning

A live browser inspection was performed against the currently deployed GitHub Pages build at `https://gemquota.github.io/nexus-aquarium/`. The aquarium canvas and panels rendered, with no visible console/runtime errors or broken resources. The canvas was reported as abstract/stylised, at roughly 13 FPS with 220 organisms. That deployment is the existing published build, not this PR branch, so it is a baseline rather than a screenshot of the new rigs.

Tuning in this PR is deliberately conservative: six body strips, no per-organism timers, no DOM animation, stable phase from simulation time/ID, and separate far/body/near passes. The branch still needs a deployed preview or local browser run with the generated PNG binaries present for final pixel-level tuning of silhouette fit, overlap, and performance.

## Known limitations

- The layered atlas is editable source artwork, while the runtime's articulated contours are procedural vector counterparts. They are not yet rigged, independently painted cut-outs extracted from the turnaround PNGs.
- The six-strip deformation approximates a flexible spine but does not preserve perfect silhouette topology at extreme bends.
- Feeding/hunting/death cues are animation clips only. The simulation must supply the corresponding state and elapsed time.
- Full multi-joint skeletal deformation, hand-authored species-specific keyframe polish, and occlusion-aware depth sorting for arbitrary camera angles remain future work.
