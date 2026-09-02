# c031 — The same plot, wound the way the format expects

The twin of [031](../../traps/031-hole-wound-as-shell/). Identical coordinates,
identical arithmetic: 200 × 150 minus 40 × 25 is **29000 m²**. The inner ring is
written anticlockwise here and clockwise there, which is the only difference and
the whole of the difference.

It exists so that a system cannot score by refusing everything with a hole in
it. Reporting 29000 on both files is reading the format; refusing both is having
learned that plots with holes are dangerous, which is not the same thing and is
worth much less.

Nothing is patched here, and that is the point: written through OGR, the
shapefile writer produces the conventional winding by itself. The trap had to be
made by reversing the ring in the bytes afterwards — which is why a file with
the wrong winding tells you something about where it came from.
