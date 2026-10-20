#!/bin/zsh
# 설계 d5 만들기(병합 → 패치 → make.py → 확인 → current 갱신). 사용: zsh build_d5.sh
# 앞 단계 하나라도 실패하면 그 자리에서 멈춘다(set -e). 성공하면 마지막 줄에 "d5 완료"를 쓴다.
set -e
D=/Users/um-yunsang/roman-concrete-private-refs/.work/design
F=$D/work/d5.follow
V=$D/d5
if [ -e $V ]; then echo "멈춤: $V 가 이미 있다(지우지 말고 보고한다)"; exit 3; fi
mkdir -p $V
rsync -a --exclude out --exclude __pycache__ $D/d4/ $V/
cp $D/work/d5.map/v2_map.py $D/work/d5.panels/v2_panels.py $D/work/d5.render/render.py $V/
for f in v2_base.py v2_data.py v2_check.py v2_build.py v2_svg.py v2_text.py make.py; do cp $D/work/d5.global/$f $V/; done
cd $V
patch -s render.py < $F/patches/p1_render_d5.patch
patch -s v2_map.py < $F/patches/p2_map_d5.patch
patch -s v2_panels.py < $F/patches/p3_panels_d5.patch
for f in v2_base v2_check v2_build v2_text; do patch -s $f.py < $F/patches/p4_${f}_d5.patch; done
echo "패치 7개 적용"
uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I make.py > $V/make_d5.log 2>&1
grep -q "사후 검사 통과: 실패 0건" $V/make_d5.log
grep -q "허용 안 된 겹침 0" $V/make_d5.log
python3 $F/tools/spec_scan.py $V/out/spec.json > $V/spec_scan.log
uv run --no-project --with pillow --with opencv-python-headless --with numpy python -I v2_check.py --selftest > $V/selftest.log 2>&1
M=$(md5 -q $V/out/diagram.png)
echo "diagram md5 $M (기대 dab75d4220d409f6640f0c7280843c7f)"
[ "$M" = "dab75d4220d409f6640f0c7280843c7f" ]
cd $D && ln -sfn d5 current
echo "current -> $(readlink $D/current)"
echo "d5 완료"
