# Species-specific articulated animation

The five-view generated turnarounds remain the painted body/orientation layer. They are not treated as animation frames.

## Runtime layers

1. The simulation supplies organism identity, species, velocity and simulation time.
2. `creature-animation.js` resolves a species rig and draws moving appendages behind the body sprite.
3. `sprite-runtime.js` selects the painted directional body pose and draws it over the rig.
4. The simulation clock and stable organism ID determine animation phase, so pausing, replaying and deterministic preview runs do not depend on browser frame rate.

## Implemented rig families

| Species | Rig family | Primary motion |
| --- | --- | --- |
| Great white, hammerhead, whale shark | Shark | Caudal oscillation, body flex, dorsal and paired pectoral fins |
| Humpback, orca | Whale | Fluked tail stroke and paired pectoral flippers |
| Bottlenose dolphin | Dolphin | Faster fluked tail stroke, body flex and pectoral flippers |
| Harbor seal, California sea lion | Pinniped | Body undulation and paired flipper strokes |
| West Indian manatee | Manatee | Slow body motion and low-amplitude paddle strokes |
| Ocean sunfish | Sunfish | Dorsal/anal foil movement and reduced tail motion |
| Pacific seahorse | Seahorse | Dorsal-fin flutter and curled tail movement |
| Moon jellyfish | Jelly | Bell pulse and independently swaying trailing tentacles |
| Green sea turtle | Turtle | Alternating foreflipper strokes and stabilising rear flippers |
| Clownfish, yellow tang, angelfish | Reef fish | Caudal oscillation, pectoral flutter and dorsal/anal fin movement |

## Animation rules

- Phase is a deterministic function of simulation time, species rate and organism ID.
- Swim speed scales stroke amplitude/frequency; stationary animals retain a low idle cycle.
- The renderer uses no per-organism timers, DOM nodes, or animation allocations.
- Appendage paths are normalised to body dimensions and drawn in one canvas pass before the body sprite.
- Horizontal facing is mirrored independently of animation phase.
- In a side-view projection, vertical screen movement does not select front/rear camera views. Those poses are only selected when an organism explicitly supplies `view`, `facing_view`, or `orientation_view`.

## Honest scope

These are procedural vector rigs, not hand-painted, frame-by-frame limb cutouts. They provide moving appendage silhouettes and species-distinct locomotion now, while preserving the generated painted body art. They do not yet provide full skeletal deformation, occlusion-aware near/far limb compositing, authored turn clips, feeding/attack/death clips, or per-frame sprite animation. Those require clean layered source artwork and dedicated animation authoring.

The original turnaround crops are static directional poses. Keep them as the body reference set; do not repurpose their five views as a five-frame swim loop.
