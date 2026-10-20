import sys
sys.path.insert(0, "out/v16_work")
import search3
tests = [dict(HUG=24, ARENA_XL=238, ARENA_CY=298.5, BOARD_H=15.0, ARENA_R=97.0, PEAK=58, T=7),
         dict(HUG=24, ARENA_XL=238, ARENA_CY=300.5, BOARD_H=15.0, ARENA_R=97.0, PEAK=58, T=7),
         dict(HUG=24, ARENA_XL=236, ARENA_CY=300.5, BOARD_H=15.0, ARENA_R=97.0, PEAK=58, T=7),
         dict(HUG=23.5, ARENA_XL=236, ARENA_CY=300.5, BOARD_H=15.0, ARENA_R=97.0, PEAK=57, T=7)]
for kw in tests:
    print(kw, search3.run(**kw))
