# 색 표본 추출: 지정 영역에서 지배색(k-means)과 비율을 출력
import sys
import cv2
import numpy as np

ART = "/Users/um-yunsang/roman-concrete-private-refs/.work/out/bj_art.png"


def dominant(img, x, y, w, h, k=5):
    roi = img[y:y + h, x:x + w].reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, labels, centers = cv2.kmeans(roi, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(-counts)
    out = []
    for i in order:
        b, g, r = centers[i]
        out.append(("#%02X%02X%02X" % (int(r), int(g), int(b)), round(100.0 * counts[i] / counts.sum(), 1)))
    return out


if __name__ == "__main__":
    img = cv2.imread(ART)
    args = sys.argv[1:]
    # 인자: name x y w h [k] 반복 (세미콜론 구분)
    for spec in " ".join(args).split(";"):
        p = spec.split()
        if not p:
            continue
        name = p[0]
        x, y, w, h = map(int, p[1:5])
        k = int(p[5]) if len(p) > 5 else 5
        print(name, (x, y, w, h), dominant(img, x, y, w, h, k))
