"""이미지 여러 장을 같은 높이로 나란히 붙인다. 사용: ra_side.py out.png h img1 img2 ..."""
import sys
import cv2, numpy as np
out, h = sys.argv[1], int(sys.argv[2])
ims = []
for p in sys.argv[3:]:
    im = cv2.imread(p)
    k = h / im.shape[0]
    ims.append(cv2.resize(im, (int(im.shape[1] * k), h), interpolation=cv2.INTER_AREA))
    ims.append(np.full((h, 8, 3), 255, np.uint8))
cv2.imwrite(out, np.hstack(ims[:-1]))
print(out)
