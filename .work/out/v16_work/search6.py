import sys
sys.path.insert(0, "out/v16_work")
import search3
base_kw = dict(HUG=24, ARENA_XL=236, ARENA_CY=305.0, BOARD_H=15.0, ARENA_R=100.0, PEAK=62, T=7)
for cw in (80, 82, 84):
    kw = dict(base_kw); kw["CORE_W"] = cw
    print(cw, search3.run(**kw))
