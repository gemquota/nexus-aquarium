# Generated species turnarounds

This directory contains five extracted static views for each of the 16 core species.

View order:
1. `front`
2. `front_three_quarter`
3. `side`
4. `rear_three_quarter`
5. `rear`

The source is `assets/sprites/generated/nexus-aquarium-generated-assets/reference-sheets/turnaround-atlas-pass-03.png`. These are directional pose selections, not animation cycles. The runtime selects a pose from organism velocity and retains procedural fallbacks for species without a matching generated view.

The extracted PNGs are supplied separately as `nexus-aquarium-sliced-sprites.zip`; extract that archive into `assets/sprites/generated/` so its `turnarounds/` directory lands here.
