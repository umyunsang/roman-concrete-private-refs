import sys
sys.path.insert(0, "out/v16_work")
import search3
tests = [dict(HUG=24, ARENA_XL=236, ARENA_CY=304.5, BOARD_H=15.0, ARENA_R=100.0, PEAK=62, T=7),
         dict(HUG=24, ARENA_XL=236, ARENA_CY=306.5, BOARD_H=15.0, ARENA_R=100.0, PEAK=62, T=7),
         dict(HUG=24, ARENA_XL=236, ARENA_CY=306.5, BOARD_H=15.0, ARENA_R=102.0, PEAK=64, T=7),
         dict(HUG=24, ARENA_XL=236, ARENA_CY=308.5, BOARD_H=15.0, ARENA_R=102.0, PEAK=64, T=7)]
for kw in tests:
    print(kw, search3.run(**kw))
