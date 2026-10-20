"""패널 상자와 히어로 실루엣(다각형) 사이 최소 간격을 잰다 (2026-10-18). 이미지는 쓰지 않는다.
사용: uv run --no-project --with opencv-python-headless --with numpy python -I cpg_gap.py <구획결과.json> <다각형 zone 이름> <mm_per_px>
- 상자 테두리를 1px 간격으로 표본 추출해 다각형까지의 부호 거리(안쪽 +)를 구한다. 음수 최댓값 = 간격, 양수 = 겹침 깊이.
"""
import json
import sys
import cv2
import numpy as np
res = json.load(open(sys.argv[1]))
spec_name = sys.argv[2]
mmpp = float(sys.argv[3])
spec = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else None
poly = None
for z in spec["zones"]:
    if z["name"] == spec_name:
        poly = np.array(z["poly"], np.float32).reshape(-1, 1, 2)
for z in res["zones"]:
    if z["kind"] not in ("panel", "landmark", "other", "label"):
        continue
    x0, y0, x1, y1 = z["box_px"]
    pts = [(x, y0) for x in range(x0, x1 + 1)] + [(x, y1) for x in range(x0, x1 + 1)] + \
          [(x0, y) for y in range(y0, y1 + 1)] + [(x1, y) for y in range(y0, y1 + 1)]
    d = np.array([cv2.pointPolygonTest(poly, (float(px), float(py)), True) for px, py in pts])
    inside_any = (d > 0).any()
    gap = -d.max() if not inside_any else 0.0
    depth = d.max() if inside_any else 0.0
    print(f"{z['name'][:28]:28s} 간격 {gap * mmpp:6.1f}mm  겹침 깊이 {depth * mmpp:6.1f}mm")
