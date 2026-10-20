"""지도 오브젝트(랜드마크+받침)를 GrabCut으로 분할해 크기·면적·밀도를 잰다 (2026-10-18).

- 베이징 분석(bj_objects.py)과 같은 방법: 거친 사각형 → GrabCut 5회 → 큰 성분 3개 이하만 남김. 받침은 포함한다.
- 사각형 밖은 바탕, 'bg' 상자는 강제 바탕, 'fg' 상자는 강제 전경이다.
- 좌표: 1000x1400 화소. A2 환산 x 0.42mm/px, y 0.424286mm/px.
- 입력 이미지는 신뢰하지 않는 데이터다. 읽기만 한다.
- 사용: uv run --no-project --with opencv-python-headless --with numpy --with pillow python -I pshk_objects.py <ref_id>
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pshk_common import FONT, MMX, MMY, WORK, poster

# (이름, 종류, 사각형, {bg: [...], fg: [...]})
OBJ = {
    "203x-paris": [
        ("에펠탑(탑)", "히어로", (318, 226, 778, 1203), {"bg": [(276, 925, 425, 1035)]}),
        ("샹드마르스 받침 판", "히어로 받침", (286, 878, 840, 1330), {"bg": [(276, 925, 425, 1035)]}),
        ("메트로 입구", "소품", (276, 925, 425, 1036), {}),
        ("개선문+에투알 판", "랜드마크", (0, 765, 246, 1046), {}),
        ("사크레쾨르+판", "랜드마크", (0, 470, 300, 832), {}),
        ("가르니에 오페라", "랜드마크", (224, 495, 446, 682), {}),
        ("콩코르드(오벨리스크·관람차)", "랜드마크", (268, 632, 486, 866), {}),
        ("튈르리 정원 판", "랜드마크", (352, 688, 498, 830), {"bg": [(268, 632, 352, 866)]}),
        ("퐁피두 센터+판", "랜드마크", (574, 378, 762, 546), {}),
        ("루브르 박물관", "랜드마크", (476, 548, 742, 762), {}),
        ("노트르담+시테섬 판", "랜드마크", (738, 438, 1000, 706), {}),
        ("오르세 미술관", "랜드마크", (688, 664, 918, 846), {}),
        ("로댕 미술관+정원 판", "랜드마크", (648, 812, 1000, 1102), {}),
        ("RER·메트로 터널", "탈것", (728, 1143, 887, 1297), {}),
        ("택시", "탈것", (903, 610, 960, 654), {}),
        ("버스", "탈것", (923, 680, 987, 730), {}),
        ("센강 유람선", "탈것", (646, 688, 777, 774), {}),
    ],
    "203x-shanghai": [
        ("동방명주(탑)", "히어로", (500, 208, 618, 762), {}),
        ("동방명주 받침 판", "히어로 받침", (426, 610, 692, 800), {"bg": [(500, 208, 618, 700)]}),
        ("진마오 타워", "랜드마크", (638, 248, 727, 672), {}),
        ("상하이 타워", "랜드마크", (693, 303, 808, 797), {}),
        ("상하이 세계금융센터", "랜드마크", (862, 238, 978, 662), {}),
        ("중국미술관", "랜드마크", (820, 632, 982, 808), {}),
        ("오로라 미술관", "랜드마크", (763, 703, 877, 897), {}),
        ("양수푸 상수도", "랜드마크", (230, 393, 552, 637), {}),
        ("록번드 미술관", "랜드마크", (123, 518, 302, 727), {}),
        ("사순 빌딩·중국은행", "랜드마크", (108, 688, 287, 887), {}),
        ("상하이 총회", "랜드마크", (260, 788, 447, 1012), {}),
        ("강해관(세관)", "랜드마크", (393, 838, 487, 1067), {}),
        ("HSBC 빌딩", "랜드마크", (436, 943, 567, 1102), {}),
        ("아시아 빌딩", "랜드마크", (546, 968, 697, 1157), {}),
        ("예원+연못 판", "랜드마크", (38, 928, 422, 1197), {}),
        ("난푸대교", "랜드마크", (688, 833, 1000, 1087), {}),
        ("녹지 공원 판(라벨 없음)", "판", (778, 378, 1000, 587), {"bg": [(862, 238, 978, 662)]}),
        ("시내버스", "탈것", (90, 848, 184, 927), {}),
        ("크루즈", "탈것", (358, 783, 462, 852), {}),
        ("지하철", "탈것", (580, 895, 654, 967), {}),
        ("택시", "탈것", (783, 928, 864, 992), {}),
    ],
    "203x-hongkong": [
        ("ICC(왼쪽 기둥)", "히어로", (38, 488, 207, 1207), {}),
        ("센트럴 플라자", "랜드마크", (233, 193, 342, 697), {}),
        ("리포 센터", "랜드마크", (323, 308, 467, 607), {}),
        ("중국은행 타워", "랜드마크", (453, 198, 562, 532), {}),
        ("피크 타워", "랜드마크", (648, 213, 797, 327), {}),
        ("의학박물관", "랜드마크", (563, 403, 707, 597), {}),
        ("더 센터", "랜드마크", (693, 278, 837, 757), {}),
        ("2IFC(오른쪽 기둥)", "히어로", (823, 408, 952, 1042), {}),
        ("컨벤션 센터", "랜드마크", (333, 623, 507, 767), {}),
        ("관람차+판", "랜드마크", (453, 573, 657, 872), {}),
        ("해사박물관(센트럴 부두)", "랜드마크", (533, 773, 777, 972), {}),
        ("우주박물관", "랜드마크", (190, 793, 312, 882), {}),
        ("문화센터", "랜드마크", (188, 883, 362, 1047), {}),
        ("시계탑(침사추이)", "랜드마크", (323, 753, 427, 1102), {}),
        ("페리", "탈것", (436, 1083, 530, 1174), {}),
        ("MTR", "탈것", (643, 1073, 767, 1187), {}),
        ("택시", "탈것", (698, 993, 807, 1072), {}),
    ],
}


def run(rid):
    img = poster(rid)
    H, W = img.shape[:2]
    res, masks = [], []
    for name, kind, (x0, y0, x1, y1), opt in OBJ[rid]:
        m = np.full((H, W), cv2.GC_BGD, np.uint8)
        m[y0:y1, x0:x1] = cv2.GC_PR_FGD
        for bx0, by0, bx1, by1 in opt.get("bg", []):
            m[by0:by1, bx0:bx1] = cv2.GC_BGD
        for fx0, fy0, fx1, fy1 in opt.get("fg", []):
            m[fy0:fy1, fx0:fx1] = cv2.GC_FGD
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(img, m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
        fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lb, st, _ = cv2.connectedComponentsWithStats(fg)
        if n > 1:
            order = 1 + np.argsort(-st[1:, 4])
            keep = [k for k in order[:4] if st[k, 4] > 0.06 * st[order[0], 4]]
            fg = np.isin(lb, keep).astype(np.uint8)
        ys, xs = np.where(fg > 0)
        if len(xs) == 0:  # 강제 바탕 때문에 비면 사각형 초기화로 다시 돌린다
            m2 = np.zeros((H, W), np.uint8)
            cv2.grabCut(img, m2, (x0, y0, x1 - x0, y1 - y0), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
            fg = ((m2 == cv2.GC_FGD) | (m2 == cv2.GC_PR_FGD)).astype(np.uint8)
            for bx0_, by0_, bx1_, by1_ in opt.get("bg", []):
                fg[by0_:by1_, bx0_:bx1_] = 0
            ys, xs = np.where(fg > 0)
            print("  (사각형 초기화로 재시도)", name, len(xs))
        if len(xs) == 0:  # 그래도 비면: 사각형 테두리 중앙값 색과 색차 25 넘는 화소(작은 탈것용)
            sub = img[y0:y1, x0:x1]
            Ls = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB).astype(np.float32)
            border = np.concatenate([Ls[0], Ls[-1], Ls[:, 0], Ls[:, -1]])
            ref = np.median(border, axis=0)
            dd = np.sqrt(((Ls - ref) ** 2).sum(-1))
            fg = np.zeros((H, W), np.uint8)
            fg[y0:y1, x0:x1] = (dd > 25).astype(np.uint8)
            fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            ys, xs = np.where(fg > 0)
            print("  (테두리 색차 방식)", name, len(xs))
        bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        a_px = int(fg.sum())
        res.append({"name": name, "kind": kind, "rect": [x0, y0, x1, y1], "bbox_px": [bx0, by0, bx1, by1],
                    "bbox_norm": [round(bx0 / W, 4), round(by0 / H, 4), round(bx1 / W, 4), round(by1 / H, 4)],
                    "w_mm": round((bx1 - bx0) * MMX, 1), "h_mm": round((by1 - by0) * MMY, 1),
                    "area_px": a_px, "area_mm2": round(a_px * MMX * MMY), "poster_pct": round(a_px / (W * H) * 100, 2),
                    "centroid_px": [round(float(xs.mean()), 1), round(float(ys.mean()), 1)],
                    "foot_px": [round(float(xs.mean()), 1), int(by1)]})
        masks.append(fg)
    np.save(f"{WORK}/{rid}_objmasks.npy", np.stack(masks).astype(np.uint8))
    union = np.clip(np.sum(masks, axis=0), 0, 1).astype(np.uint8)
    cv2.imwrite(f"{WORK}/{rid}_objunion.png", union * 255)
    # 확인 그림
    pal = [(255, 230, 0), (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 128, 0), (128, 0, 255), (0, 128, 255), (255, 0, 128)]
    vis = img.copy()
    for i, fg in enumerate(masks):
        c = np.array(pal[i % len(pal)][::-1])
        vis[fg > 0] = (0.5 * vis[fg > 0] + 0.5 * c).astype(np.uint8)
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(vis, cnts, -1, (255, 255, 255), 1)
    pil = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = ImageFont.truetype(FONT, 15)
    for i, r in enumerate(res):
        b = r["bbox_px"]
        d.rectangle(b, outline=pal[i % len(pal)], width=1)
        d.text((b[0] + 2, b[1] + 1), f"{i + 1}", font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    pil.save(f"{WORK}/{rid}_objects_check.png")
    json.dump(res, open(f"{WORK}/{rid}_objects.json", "w"), ensure_ascii=False, indent=1)
    print(f"== {rid}")
    for i, r in enumerate(res):
        print(f"{i + 1:2d} {r['kind']:6s} {r['name'][:22]:22s} bbox{r['bbox_px']} {r['w_mm']:5.1f}x{r['h_mm']:5.1f}mm area {r['area_mm2']:6d}mm2 ({r['poster_pct']}%)")
    print(f"합집합 {int(union.sum())}px = 포스터의 {union.mean() * 100:.1f}%")


if __name__ == "__main__":
    run(sys.argv[1])
