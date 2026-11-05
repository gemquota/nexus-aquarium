# Aquarium visual validation

The browser workflow starts the static dashboard in Chromium, captures three camera scales, and uploads the captures as the `nexus-aquarium-visual-captures` artifact.

## Automated coverage

- The manifest loads without failed sprite requests.
- The local preview contains 220 organisms across at least 10 species.
- Organisms remain inside the water column and occupy multiple depth bands.
- Preview positions change between frames, not just the decorative surface.
- Surface-wave displacement changes with simulation time and increases with swell.
- Measured fish sprite dimensions remain visible at overview zoom and scale proportionally at normal and close zoom.
- The canvas remains usable at zoom 0.25x, 6x and 24x.
- No uncaught browser page errors occur.
- Backend tests verify shoal counts, horizontal clustering, depth bands, schooling neighbourhood scale and world-relative movement.

## Manual review checklist

Use the CI screenshots as a quick comparison, then inspect the live Pages build on a phone and desktop.

| Area | What to inspect |
|---|---|
| Swimming | Fish translate continuously; tail undulation is visible at normal/close zoom; direction changes do not snap or teleport at backend refresh boundaries. |
| Proportions | Small fish remain distinguishable at overview; fish, sharks, rays, turtles and marine mammals retain recognisable relative sizes at 6x and 24x. |
| Shoals | Same-species groups read as schools rather than evenly spaced particles; individuals do not overlap excessively or collapse into a single blob. |
| Depth | Surface skimmers stay near the waterline; reef, pelagic and deepwater species occupy distinct layers; benthic life remains near the seabed. |
| Waves | Surface motion travels laterally, responds to swell, remains attached to the waterline while panning/zooming, and does not drift independently of the simulation clock. |
| Mobile | Touch pan and pinch zoom remain responsive; no controls or canvas content are clipped by the viewport. |

## Interpretation

The browser job exercises the local static preview, not a live remote simulation service. It verifies renderer behaviour and captures repeatable views; it cannot replace checking real backend snapshots, saved-world restoration, or the deployed Pages build on physical devices.
