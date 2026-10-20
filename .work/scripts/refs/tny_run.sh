#!/bin/zsh
# 도쿄·뉴욕2·뉴욕1 레퍼런스 정밀 실측 파이프라인(재현용). 내려받은 이미지 폴더 밖(/tmp)에서 실행한다.
# 출력: .work/out/refs-analysis/ (tny_* 와 203x-tokyo_*, 203x-newyork2-centralpark_*, 203x-newyork_*)
set -e
S=/Users/um-yunsang/roman-concrete-private-refs/.work/scripts/refs
PY=(uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I)
PYC=(uv run --no-project --with opencv-contrib-python-headless --with numpy python -I)
cd /tmp
$PY $S/tny_reg.py                      # 1) 고해상 타일 3장 정합 → 2000x2800 합성 아트
$PY $S/tny_angles.py                   # 2) LSD 선분 방향 히스토그램(투영 각)
for r in 203x-tokyo 203x-newyork2-centralpark 203x-newyork; do
  $PY $S/tny_inkmask.py $r             # 3) 바탕 모델·잉크 마스크
  $PY $S/tny_classmap.py $r            # 4) 바탕·길·물·글자·오브젝트·땅·하늘 클래스
done
for r in 203x-newyork2-centralpark 203x-newyork; do
  $PY $S/tny_grabcut_lm.py $r          # 5) 랜드마크 GrabCut(뉴욕 2점)
done
for r in 203x-tokyo 203x-newyork2-centralpark 203x-newyork; do
  $PY $S/tny_objects.py $r             # 6) 랜드마크·코어 군·밀도
  $PYC $S/tny_network.py $r            # 7) 길·강 폭·블리드·접속
  $PY $S/tny_gaps.py $r                # 8) 이웃 간격
  $PY $S/tny_label_angles.py $r        # 9) 라벨 글줄 기울기·세로획
  $PY $S/tny_geo_fit.py $r             # 10) 압축 지리(닮음변환·거리 법칙)
  $PY $S/tny_assemble.py $r            # 11) 구획 종합 JSON + 확인용 구획 이미지(<ref>_zones.png)
done
$PY $S/tny_combine.py                  # 12) 세 점 핵심 수치·1차 실측 정정 모음
