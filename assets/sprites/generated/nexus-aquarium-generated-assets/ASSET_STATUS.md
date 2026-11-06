# NEXUS Aquarium generated asset bundle

## Contents
- `catalogues/`: overview/reference atlases.
- `creatures/sharks/great-white/`: dedicated Great White Shark reference/animation sheets.
- `reference-sheets/`: seven additional generated turnaround-atlas passes.

## Production status
The files in `reference-sheets/` are **composite reference atlases**, not 16 individually isolated species sheets. They are useful for visual direction and turnaround reference, but are not ready to drop into the runtime as individual sprites. Some panels may have inconsistent views or anatomy; inspect before slicing.

The required five-view standard is **front, front three-quarter, side, rear three-quarter, rear**. The 16-species set is: Great White Shark, Hammerhead Shark, Whale Shark, Humpback Whale, Orca, Bottlenose Dolphin, Harbor Seal, California Sea Lion, West Indian Manatee, Ocean Sunfish (Mola Mola), Pacific Seahorse, Moon Jellyfish, Green Sea Turtle, Clownfish, Yellow Tang, and Angelfish.

## Remaining work
1. Create one separate sheet per species, with exactly five consistently oriented views.
2. Use transparent backgrounds and isolate each pose with clean margins.
3. Verify alpha, anatomy, view ordering, scale, pivots, and consistent outlines.
4. Slice validated poses into runtime sprites and add animation frames where required.
5. Add per-species metadata and a runtime manifest, then test rendering at multiple zoom levels.

The 16 individual production sheets and runtime integration are not complete.
