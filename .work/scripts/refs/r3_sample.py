"""N 좌표 점들의 색(Lab·RGB)을 5×5 중앙값으로 출력한다. 사용: r3_sample.py <ref> x,y x,y ..."""
import sys

import numpy as np

sys.path.insert(0, "/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs")
from r3_common import lab, load_norm  # noqa: E402

ref_id = sys.argv[1]
im, _ = load_norm(ref_id)
L = lab(im)
for tok in sys.argv[2:]:
    x, y = [int(v) for v in tok.split(",")]
    p = L[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3)
    c = im[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3)
    print("(%4d,%4d) Lab %s RGB %s" % (x, y, np.round(np.median(p, 0), 1), np.median(c, 0)[::-1].astype(int)))
