# 1차 조사 D·E: 3D→플랫 벡터, AI 생성·벡터화

> **배경**: 로마 콘크리트를 주제로 한 A2 세로 인포그래픽 포스터를 준비하고 있다. 정보 디자인 벤치마크는 한국 스튜디오 203X의 포스터(베이징, 신문 제작 과정)이고, 2.5D/3D 모델의 수준 기준은 사용자가 준 아이소메트릭 미니어처 콜로세움 디오라마 이미지다. 이 문서는 이를 위한 오픈소스 도구·플러그인·스킬·하네스 조사 가운데 레인 D(3D→플랫 벡터)와 레인 E(AI 생성·벡터화)의 결과를 한국어로 옮긴 것이다.
>
> **원자료**
> - `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/wf1/lanes/D-3d-to-flat-vector.json`
> - `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/wf1/lanes/E-ai-gen-and-vectorize.json`
>
> **용어 정리**: 원문이 언급하는 "r23", "VectorCraft 트레이싱", "회화풍(painterly) 경로" 등 이전 파이프라인은 모두 **사용자가 폐기한 이전 작업**이다. 아래 측정 중 일부는 그 폐기된 결과물을 시험 입력으로만 쓴 것이다.

---

# 제1부. 레인 D: 3D에서 깔끔한 플랫 셰이딩 벡터로 (지오메트리 우선 아이소메트릭 벡터) + 로마 랜드마크용 오픈 3D 모델 소스

## D-1. 한눈에 보는 결론

- 203X 룩은 픽셀이 아니라 **지오메트리에서 나온 도형**이다. 메시 면을 직접 투영하면 엣지가 정확하고 패스 수가 "오브젝트당·톤당 도형 하나"로 줄어든다(시험: 보이는 면 420개 → 병합된 SVG 패스 17개, 9.6 KB).
- 가장 적합한 경로는 **Blender 5.2 LTS(`blender -b`) + 커스텀 bpy 면 투영 스크립트 + Shapely 2.x 은면 제거·병합**이다. 모두 로컬에 설치돼 있고 뷰포트 없이 헤드리스로, 에이전트가 구동할 수 있다.
- 노이즈 조각·밝은 점의 원인은 세 가지로 검증됐다. (1) 맞닿은 독립 패스의 안티앨리어싱 이음매(같은 색 0.6 px 스트로크로 5,939 → 0 픽셀), (2) Blender 5.2 기본값(dither 1.0, AgX)이 더하는 팔레트 밖 색(88색 → dither 0에서 14색), (3) 연속톤 텍스처는 포스터라이즈만 될 뿐 면으로 복원되지 않는다는 점이다.
- 뷰포트가 필요한 기성 익스포터(Scene To SVG, Grease Pencil SVG 내보내기)는 헤드리스에서 실패했다. 지오메트리를 쓸 수 없을 때만 AA를 끈 Workbench 렌더 + 정확한 팔레트 VTracer를 폴백으로 쓴다.
- 모델 소스는 저폴리 CC0/CC-BY(Poly Pizza, Sketchfab, Kenney, Quaternius)를 블록아웃·참조로만 쓰고, 포토그래메트리 스캔은 투영하지 않는다.

## D-2. 핵심 발견

1. **203X 룩은 지오메트리에서 파생된 도형에서 나온다.** 사용자가 폐기한 이전 작업의 경로는 그 도형을 픽셀에서 얻으려 했다. 회화풍이나 AI 래스터에 VTracer/VectorCraft를 돌리면 트레이서가 색 군집으로 면 경계를 추측한다. 브러시 텍스처, AO, 그라디언트, 업스케일러 노이즈가 모두 폴리곤이 되고, 그래서 한 장면이 패스 약 19k개, 흔들리는 엣지, 깨진 아이소 축으로 끝났다. 메시 면을 직접 투영하면 엣지가 정확하고 패스 수는 "오브젝트당·톤당 도형 하나"가 된다. 스모크 테스트에서 보이는 면 420개가 병합된 SVG 패스 17개(9.6 KB)가 됐다.

2. **노이즈 조각과 밝은 점에는 검증된 메커니즘이 세 가지 있다.**
   - (1) **맞닿은 독립 패스가 만드는 안티앨리어싱 결합(conflation) 이음매.** 그것 말고는 완벽한 17패스 SVG를 1600 px 폭으로 렌더하자 내부 픽셀 5,939개에서 배경이 비쳤다. 같은 색 0.6 px 스트로크('overdraw', three.js SVGRenderer가 쓰는 것과 같은 기법)를 더하자 0이 됐다. T자 접점에서 밝은 종이나 배경이 비치면 정확히 밝은 점처럼 보인다.
   - (2) **Blender 5.2 기본값이 팔레트에 없는 색을 더한다**: dither_intensity=1.0과 AgX 뷰 변환. 14톤 플랫 Workbench 렌더가 dither를 켜면 고유색 88개, dither 0이면 14개였다.
   - (3) **연속톤 원본 텍스처는 포스터라이즈만 될 뿐, 면으로 복원되지 않는다.**

3. **Blender 5.2.2 LTS(설치됨)에는 Freestyle SVG Exporter가 더 이상 번들되지 않는다.** 4.2에서 extensions.blender.org로 옮겨져 v1.0.0으로 'offered as is, with limited support'(있는 그대로, 제한적 지원) 상태로 제공된다. 유일한 내장 SVG 애드온 io_curve_svg는 임포터다. 코어 SVG/PDF 작성기는 Grease Pencil v3 연산자 wm.grease_pencil_export_svg/pdf(use_fill, stroke_sample, use_uniform_width, use_clip_camera)다. 5.1에서 구멍 있는 채우기(fill_id)가, 5.2에서 Line Art 'Fill Strokes' 옵션과 Delaunay 채우기 솔버가 추가됐다. 로컬 RNA에서 fill_strokes를 확인했다.

4. **면 중심점(centroid) 기준 화가 정렬은 큰 면에서 눈에 띄게 실패한다.** 시험에서 바닥 쿼드 하나가 경기장 링의 뒤쪽 절반을 가렸다. 쌍별 국소 깊이 테스트로 고쳤다. 두 면의 화면 공간 깊이 평면을 2D 겹침 영역 안의 한 점에서 평가하고, 더 먼 면에서 겹침을 뺀다. Shapely 2.1(STRtree + difference + union_all(grid_size=0.01))로 면 420개에 대해 약 0.25초 만에 정확하고, 틈이 없고, 서로 겹치지 않는 벡터 영역을 얻었다. 일반 unary_union은 부동소수점 슬리버를 남겼고, 이어서 마이터 버퍼 닫기(mitre-buffer close)를 하자 한 그룹이 면적 0으로 붕괴했다. 따라서 스냅 라운딩된 union_all이 필요하다.

5. **3D 뷰포트가 필요한 기성 익스포터는 Blender 5.2 헤드리스에서 실패한다.** Scene To SVG는 `AttributeError: 'NoneType' object has no attribute 'region_3d'`를 냈다. Line Art 스트로크의 GP SVG 내보내기는 퇴화한 좌표(viewBox 높이 0, y 약 -4e6)를 만들었다. world_to_camera_view를 쓰는 커스텀 bpy 스크립트는 뷰포트 없이 `blender -b`에서 동작하므로, 에이전트가 가장 구동하기 쉬운 선택지다(Bash 또는 Blender MCP execute_blender_code).

6. **지오메트리를 쓸 수 없을 때(고밀도 스캔, 불리언)의 깔끔한 폴백도 결국 지오메트리를 인식하는 래스터다.** Workbench를 Flat 조명, 면별 색 속성(colour attribute), render_aa=OFF, 뷰 변환 Standard, dither 0으로 렌더한 뒤, 정확한 톤을 담은 --palette-file로 VTracer를 돌린다. 같은 장면에서 18패스로 깔끔했지만, 정확한 투영과 비교하면 곡선에 픽셀 계단식 흔들림이 보인다. 폴백으로만 쓴다.

7. **곡면(판테온 돔, 드럼, 콜로세움 외피)은 면별로 양자화하면 들쭉날쭉한 패싯 띠로 포스터라이즈된다.** 203X는 원통(열차, 인쇄 롤러)에 매끄러운 벡터 그라디언트를 쓴다. 오브젝트 실루엣을 병합해 SVG linearGradient나 radialGradient를 적용하거나, 띠 경계가 자오선을 따를 만큼 세그먼트를 충분히 쓴다. 3밴드 규칙은 평면에만 적용한다.

8. **에이전트 도구.** 이 세션에 연결된 Blender MCP는 ahujasid의 'MCP for Blender'다(로컬 애드온 v1.8, 저장소 이름이 ahujasid/mcp-for-blender로 바뀜, ★31.4k, PyPI 2.1.9, 2026-10-06). 도구는 execute_blender_code, look, Poly Haven/Sketchfab/Poly Pizza 검색·가져오기, generate_3d다. 공식 Blender Lab MCP도 있다(projects.blender.org/lab/blender_mcp, GPL-3.0, v1.0.3 2026-09-11, Blender 5.1+ 필요). 둘 다 벡터 내보내기는 하지 않으며, 빠진 조각이 바로 투영 스크립트다.

9. **모델 소스.** Sketchfab의 저폴리 CC-BY 콜로세움(면 11.8k–38k)과 Poly Pizza의 CC0 콜로세움은 블록아웃이나 참조 지오메트리로 적합하다. 포토그래메트리 스캔(판테온 0.67–1.5M면, 콜로세움 0.76–9.3M면)은 노이즈 패싯을 수천 개 만들므로, 깨끗한 저폴리 지오메트리를 다시 모델링할 때 참조로만 쓴다. 플랫 아이소 벡터에는 손으로 만들거나 Geometry Nodes로 절차적으로 만든 랜드마크(아케이드 배열, 관람석 단, 격자천장 코퍼)가 내려받은 메시보다 낫다.

10. **작업 환경 메모.** 조사 도중(약 12:09) 사용자 지시로 이전 작업 폴더(artwork/, .planning/)가 삭제됨(정상). 확인 시점의 프로젝트 루트에는 docs/, .tools/, .remember, .ruff_cache만 있었다. 203X 원본 크롭은 현재 `docs/references/assets/203x/originals/` 에 있다. 이 레인은 프로젝트를 전혀 수정하지 않았고, 모든 시험은 scratchpad에서 실행했다.

## D-3. 권장 파이프라인

1. **모델링.** 각 랜드마크를 Blender 5.2에서 일러스트용 저폴리 지오메트리로 모델링한다. 대상은 아케이드 배열과 기초 컷어웨이가 있는 콜로세움 외피, 폼페이 유적, 판테온 드럼과 돔, 수도교 수로, 포르투스 방파제(mole)와 배, 균열 단면 슬래브다. 반복되는 아치·관람석 단·코퍼는 Geometry Nodes로 만들고, CC0/CC-BY 저폴리 모델(Poly Pizza CC0 콜로세움, Sketchfab CC-BY 저폴리 콜로세움, Kenney/Quaternius 소품과 인물)은 블록아웃이나 참조로만 쓴다. 면은 평면으로 유지하고, 머티리얼 구역별로 오브젝트를 나누고, 불리언은 적용(apply)해 둔다. 스캔은 투영하지 않는다.
2. **카메라 고정.** 포스터 전체에 직교 카메라 회전 하나를 고정한다. 정 아이소는 (54.736°, 0, 45°), 2:1이면 (60°, 0, 45°)다. 랜드마크마다 카메라를 하나씩 두고 각자의 ortho_scale로 큐레이션한 상대 크기를 정하며, 렌더 해상도를 SVG 단위로 쓴다.
3. **톤 모델.** 재료(콘크리트, 트래버틴, 벽돌, 목재, 물, 인물)마다 5–8색 팔레트 계열을 둔다. 각 평면은 고정 키 라이트에 대한 월드 노멀에 따라 위·왼쪽·오른쪽 톤 중 하나를 받으므로 3밴드가 된다. 선택적 면 속성으로 강조색이나 그림자 형태를 덮어쓸 수 있다. 곡면 오브젝트는 병합한 실루엣에 SVG linear 또는 radial 그라디언트를 쓴다(203X가 원통에 하는 방식).
4. **헤드리스 지오메트리 내보내기.** `blender -b --python project.py`가 후면 컬링된 면(2D 점, 면별 화면 공간 깊이 평면, 톤, 오브젝트/머티리얼 id)을 JSON으로 덤프한다. 뷰포트가 필요 없다. 스크립트: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/scripts/build_and_project.py`
5. **픽셀이 아니라 지오메트리에서 벡터화.** Shapely 2.x에서 중심점 화가 정렬 대신 STRtree 쌍별 국소 깊이 테스트(각 2D 겹침 안에서 깊이 평면을 비교한 뒤, 더 먼 면에서 겹침을 뺌)를 쓴다. 그다음 (오브젝트, 톤)별로 `shapely.union_all(..., grid_size=0.01)`, 약 0.05 px simplify를 거쳐 `<g id=landmark>/<path id=object-tone>`을 쓴다. 스크립트: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/scripts/hsr_merge_svg.py`. 같은 색 0.5–0.6 px 스트로크를 더하거나 뒤에서 앞으로 쌓은 실루엣을 내보내 맞닿은 도형에 AA 이음매가 생기지 않게 한다.
6. **선화(원할 경우).** 블록 줄눈, 아치 테두리, 균열선에는 Line Art(crease, edge marks, intersections)를 쓴다. 평가된 스트로크 점을 읽어 같은 카메라로 SVG 폴리라인으로 투영하거나, Blender MCP를 통해 GUI에서 GP SVG 익스포터를 실행한다. 헤드리스 GP 내보내기는 퇴화한 좌표를 만들었다.
7. **폴백(깨끗하게 투영할 수 없는 것).** Workbench(Flat 조명, Attribute 색, render_aa OFF, 뷰 변환 Standard, dither 0)로 2–4배 렌더한 뒤, 정확한 톤을 담은 --palette-file로 VTracer polygon 모드를 돌린다. 또는 OpenCV로 라벨 래스터를 폴리곤화하고 mapshaper의 위상 보존 단순화를 돌린다. 최종 아트에 회화풍이나 AI 래스터를 트레이싱하지 않는다.
8. **Figma 조립.** SVG 그룹을 Figma로 가져온다. 그레인이나 텍스처 오버레이는 별도 레이어에 두어 지오메트리를 깨끗하게 유지하고, 타이포그래피, 지시선 라벨, 측면 패널은 Figma에서 배치한다.
9. **랜드마크별 QA 게이트.** 패스 수와 고유 채우기 수(팔레트 규율)를 점검하고, #00ff00 배경으로 렌더해 내부 초록 픽셀 0개를 요구하는 이음매 시험을 한다. Blender MCP look이나 rsvg-convert로 시각 점검한다.

## D-4. 실제로 실행한 검증·시험과 결과

### D-4-1. 노이즈 원인 관련 실험 수치

| 실험 | 조건 | 결과 |
|---|---|---|
| AA 결합 이음매 | clean.svg를 #00ff00 배경에 rsvg-convert 1600 px로 렌더 | 내부 배경 비침 픽셀 5,939개 → 각 패스에 같은 색 0.6 px 스트로크를 더하면 0 |
| 렌더 디더 | 면별 색 속성 Workbench 플랫 렌더(14톤) | dither 1.0: 고유색 88개 / dither 0: 14개(의도한 팔레트) |
| 5.2.2 팩토리 기본값 | `blender -b` 확인 | render.dither_intensity=1.0, filter_size=1.5, Workbench render_aa='8', view_transform='AgX' |
| 지오메트리 투영 | 보이는 면 420개, 쌍별 국소 깊이 + union_all(grid_size=0.01) | 17패스, 9,645바이트 SVG, 0.25초 |
| 래스터 폴백 | AA 끈 렌더, VTracer 1.0.0-alpha.4 polygon·cutout·14톤 --palette-file | 18패스, 20,709바이트. 기본 정밀도에서 dither 0과 1의 출력이 동일. 곡선 엣지에 계단식 흔들림 |
| 회화풍 경로(사용자가 폐기한 이전 작업) | VTracer/VectorCraft로 회화풍·AI 래스터 트레이싱 | 한 장면에 패스 약 19k개 |

### D-4-2. 전체 시험 기록

1. `blender --version` → 'Blender 5.2.2 LTS'(빌드 2026-09-15). df: 여유 공간 9.2 GiB.
2. `ls .../Blender.app/Contents/Resources/5.2/scripts/addons_core` → bl_pkg, cycles, hydra_storm, io_anim_bvh, io_curve_svg, io_mesh_uv_layout, io_scene_fbx, io_scene_gltf2, node_wrangler, pose_library, rigify, ui_translate, viewport_vr_preview. Freestyle SVG exporter는 번들되지 않았다. 사용자 애드온은 blender_mcp.py(ahujasid, bl_info 1.8) 하나뿐이다.
3. `blender -b --python-expr`: bpy.ops.wm에 grease_pencil_export_svg, grease_pencil_export_pdf, grease_pencil_import_svg가 있다. SVG 옵션은 use_fill, selected_object_type, frame_mode, stroke_sample, use_uniform_width, use_clip_camera다. GreasePencilLineartModifier는 fill_strokes('Generate filled strokes instead of only outline'), use_shadow, use_light_contour, shadow_region_filtering을 노출한다.
4. 5.2.2 팩토리 기본값: render.dither_intensity=1.0, filter_size=1.5, Workbench render_aa='8', view_transform='AgX'.
5. build_and_project.py(시험 장면: 바닥 슬래브, 2중 링 경기장, 모래, 판테온 같은 드럼과 돔, 상자 3개; 직교 카메라 54.736/0/45) → FACES_VISIBLE 420.
6. hsr_merge_svg.py v1(중심점 정렬): 큰 바닥 쿼드가 링과 돔의 뒤쪽을 잘못 가렸다. v2(STRtree를 쓴 쌍별 국소 깊이)는 가림이 올바랐다. 일반 unary_union은 부동소수점 슬리버를 남겼고, 마이터 버퍼 닫기는 안쪽 링 윗면을 면적 0으로 붕괴시켰다. `shapely.union_all(grid_size=0.01)`로 바꾸자 해결됐다. 최종: 면 420개 → 17패스, 9,645바이트 SVG, 0.25초. 미리보기: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/out/clean.png`
7. 면별 색 속성을 쓴 Workbench 플랫 렌더: dither 1.0 → 고유색 88개, dither 0 → 14개(의도한 팔레트).
8. VTracer 1.0.0-alpha.4(polygon, cutout, 정확한 14톤 --palette-file)를 AA 끈 렌더에 적용 → 18패스, 20,709바이트. 기본 정밀도에서 dither 0과 1의 출력이 동일했다. 나란히 비교한 크롭에서 정확한 투영 대비 곡선 엣지의 계단식 흔들림이 보인다: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/out/cmp.png`
9. 이음매 시험(clean.svg를 #00ff00 배경에, rsvg-convert 1600 px): 내부 배경 비침 픽셀 5,939개. 각 패스에 같은 색 0.6 px 스트로크를 더하면 0개.
10. Line Art 헤드리스: `grease_pencil_add(type='LINEART_SCENE')`가 스트로크 68개를 평가했다. -b 모드의 wm.grease_pencil_export_svg는 퇴화한 지오메트리를 썼다(use_clip_camera=True: y 약 -4,039,870; False: viewBox '0 0 1155.78 0'). 따라서 GUI 뷰포트가 필요하다.
11. Craszh Scene To SVG(scene_to_svg.py)를 5.2.2 -b에서 카메라 오브젝트와 함께 로드 → `AttributeError: 'NoneType' object has no attribute 'region_3d'`(camera_object_to_camerainfo). 따라서 GUI 뷰포트가 필요하다.
12. Freestyle SVG Exporter 확장 zip(sha256 d72191a8...b, 인덱스와 일치; 7,691바이트)은 검사만 했다. SVGFillBuilder가 오브젝트별 ExternalContour 스트로크를 병합하고, 채우기 = 머티리얼 diffuse, evenodd 방식이다. 면별 톤은 없다.
13. three.js SVGRenderer.js(r186) 소스 확인: 요소별 Projector 화가 정렬, overdraw=0.5, MeshBasic/Lambert/Phong/Standard/Normal 머티리얼 지원.
14. extensions.blender.org API(항목 1,537개)를 svg/vector/isometric으로 필터 → freestyle_svg_exporter 1.0.0, export_curve_as_svg 2.0.0, isometric_scene_setup 1.0.1, stb_section_toolbox 0.0.2.
15. Sketchfab /v3/search(downloadable)로 colosseum, colosseo, pantheon, aqueduct, crane, ship, portus 검색 → 면 11.8k–38k의 CC-BY 저폴리 콜로세움, Aquaeduct 6.6k, Treadwheel Crane 67.5k, 판테온 스캔 0.67–1.49M면. 포르투스 전용 모델은 찾지 못했다.
16. Poly Pizza 페이지: CreativeTrio의 Colosseum은 CC0(FBX/glTF), Poly by Google의 Coliseum은 CC-BY 3.0. Poly Haven API: 모델 521개, 로마 관련 없음.
17. gh api 저장소 점검: ahujasid/mcp-for-blender ★31,419(2026-10-06 푸시, MIT); Blender Lab MCP(projects.blender.org API) GPL-3.0, v1.0.3 2026-09-11; mrossini-ethz/vector-render 마지막 푸시 2021; Craszh/BlenderModelToSVG 마지막 푸시 2023; mapshaper v0.7.88 2026-10-17; elchininet/isometric v4.0.0; zdog v1.1.1(2019).

## D-5. 후보 도구 표

### D-5-1. 후보 목록 (적합도 높은 순)

| 이름 | 단계 | 하는 일 | 적합도(1~5) | 라이선스 | 오픈소스 여부 | 유지보수 상태 | 주의사항 | URL |
|---|---|---|---|---|---|---|---|---|
| 커스텀 bpy 면 투영 + Shapely HSR/병합 스크립트(이 레인에서 스모크 테스트함) | 플랫 렌더 / 벡터 저작(3D→SVG) | blender -b에서 실행한다. 메시 면을 후면 컬링하고, 고정된 직교 아이소 카메라로 world_to_camera_view 투영하고, 고정 키 라이트 대비 월드 노멀로 머티리얼마다 3톤을 배정하고, 면별 2D 점과 깊이 평면을 덤프한다. 이어서 시스템 Python의 Shapely 단계가 쌍별 국소 깊이 은면 제거를 하고 (오브젝트, 톤)별로 병합해 id가 붙은 SVG 패스를 쓴다. | 5 | Blender GPL-2.0+; Shapely BSD-3; 스크립트는 이 레인 조사자가 작성(scratchpad) | 예 | Blender 5.2.2 LTS 빌드 2026-09-15; Shapely 2.1.2 | 프로토타입일 뿐이다. 서로 관통하는 면은 분할이 필요하다(BSP 또는 평면 클리핑). 쌍별 테스트는 평면이고 교차하지 않는 면을 가정한다. 곡면은 패싯 띠 대신 그라디언트 채우기가 필요하다. 맞닿은 도형은 AA 이음매를 피하려면 0.5–0.6 px 같은 색 스트로크나 적층 순서가 필요하다(측정됨). 스크립트: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/scripts/build_and_project.py`, `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane3d/scripts/hsr_merge_svg.py` | https://docs.blender.org/api/current/bpy_extras.object_utils.html |
| Blender 5.2 LTS(모델링, Geometry Nodes, 직교 아이소메트릭 카메라, Workbench/EEVEE 플랫 셰이딩) | 모델링 / 플랫 렌더 | 저폴리 모델링과 아케이드·관람석 단·코퍼용 절차적 배열. 정 아이소(54.736°, 0, 45°) 또는 2:1 다이메트릭(60°, 0, 45°) 직교 카메라를 지원한다. Workbench는 Attribute/Material 색과 render_aa OFF를 쓰는 Flat 조명을, EEVEE는 정확한 톤 밴드를 위한 상수 ColorRamp + Shader-to-RGB를 제공한다. | 5 | GPL-2.0-or-later | 예 | 5.2.2 LTS, 빌드 2026-09-15 | 기본값이 정확한 색 렌더를 망친다: dither_intensity 1.0, 뷰 변환 AgX, 픽셀 필터 1.5 px, Workbench AA 8 샘플. 래스터→벡터 폴백에는 dither 0, Standard, AA OFF로 설정한다. | https://www.blender.org/download/ |
| Shapely 2.x(GEOS), 2D 은면 제거·병합용 | 벡터 저작(은면 제거 / 불리언 병합) | STRtree 공간 질의를 곁들인 폴리곤 difference·union, 스냅 라운딩 union_all(grid_size)과 simplify. 투영된 면을 서로 겹치지 않는 가시 영역으로 바꾸고, 같은 평면·같은 톤 패싯을 병합한다. | 5 | BSD-3-Clause | 예 | 2.1.2 설치됨 | Blender 밖에서 실행하거나 별도 venv에 pip로 설치한다. Blender 번들 Python에는 Shapely가 없다. union_all(grid_size=...)을 쓸 것. 시험에서 일반 unary_union은 부동소수점 슬리버를 남겼고, 이어진 마이터 버퍼 닫기가 한 그룹을 면적 0으로 붕괴시켰다. | https://github.com/shapely/shapely |
| MCP for Blender(ahujasid/mcp-for-blender, 구 blender-mcp), 이 세션에 연결된 서버 | MCP / 에이전트 하네스 | 소켓 애드온 + MCP 서버. 도구: execute_blender_code, look(뷰포트, 카메라, 다각도 시트, 렌더), search_assets/import_asset(Poly Haven, Sketchfab, Poly Pizza), generate_3d(Tripo, Hunyuan3D, Rodin), get_addon_status, 텔레메트리 제어. 선택적 BLENDER_MCP_SAFE_MODE가 있다. | 4 | MIT | 예 | ★31,419; 2026-10-06 푸시; PyPI mcp-for-blender 2.1.9(2026-10-06) | 사용자가 실행 중인 Blender에서 임의 Python을 실행하므로, 사본을 저장하지 않은 채 프로젝트 .blend 파일을 건드리지 말 것. 로컬 애드온(v1.8)이 PyPI 서버보다 뒤처질 수 있으며 README에 업데이트 명령이 있다. 자체 벡터 내보내기는 없다. | https://github.com/ahujasid/mcp-for-blender |
| Sketchfab(CC 라이선스 다운로드 가능 모델: 콜로세움, 판테온, 수도교, 크레인, 배) | 에셋(3D 모델) | 확인한 검색 API 결과. 저폴리 CC-BY 콜로세움: alexanderleth 37,816면(https://sketchfab.com/models/c3c5157559344c74b2c0bacc89036692), Carlos.Maciel 11,801(https://sketchfab.com/models/e749705838044be78ced42205f9f9dda), dany3design 'Colosseo' 18,536(https://sketchfab.com/models/20365822476042cc88cffe613a56e83e), 'Low Poly Roman Amphitheatre' 14,603(https://sketchfab.com/models/ee2aaad3ef1446ee9a69e5c9bde1fca4). 기타: 'Aquaeduct' 6,608(https://sketchfab.com/models/d1b68f033efc486a98389676b37f6064), 'Treadwheel Crane' 67,526(https://sketchfab.com/models/1129cebe176442d19aee2ef2459e1e1f), 'Roman Liburna' 602k(https://sketchfab.com/models/0d84c39a677e41e8964cc4f1ea51f504). 판테온 스캔은 CC-BY, 0.67–1.49M면. | 4 | 모델별. 나열한 것은 CC Attribution(CC-BY 4.0). 일부 로마 결과는 BY-NC 또는 BY-NC-ND(상업적 사용 시 피할 것) | 아니요 | 운영 중인 플랫폼 | 토폴로지는 검사하지 않았다. 스캔(판테온, 다수의 콜로세움)은 플랫 투영에 너무 조밀하고 노이즈가 많으므로 참조로만 쓰고 다시 모델링한다. CC-BY는 포스터에 크레딧 줄이 필요하다. | https://sketchfab.com/search?q=colosseum&type=models&features=downloadable |
| Poly Pizza(CC0 / CC-BY 저폴리 모델) | 에셋(저폴리 모델) | 저폴리 모델 라이브러리. 확인: CreativeTrio의 'Colosseum', CC0, FBX/glTF(https://poly.pizza/m/83ftBPyiSf). Poly by Google의 'Coliseum', CC-BY 3.0, OBJ/glTF(https://poly.pizza/m/cvCqP8aHvn5). 검색 결과에 Roman Arch, Roman Pillars, 로마 군단병/백인대장 모델도 있다. | 4 | 모델별: CC0 또는 CC-BY 3.0 | 예 | 운영 중인 플랫폼 | 아치, 기둥, 군단병 모델의 라이선스는 개별 확인하지 않았다. 사이트 자체는 오픈소스가 아니고, 콘텐츠가 오픈이다. | https://poly.pizza/m/83ftBPyiSf |
| Blender Lab 공식 MCP 서버 | MCP / 에이전트 하네스 | Blender Foundation(Blender Lab)의 MCP: TCP 소켓 애드온과 MCP 릴레이 프로세스. Python API 접근, 문서 조회, 장면 분석, 데이터 블록 질의를 제공한다. | 3 | GPL-3.0 | 예 | v1.0.3 2026-09-11 릴리스; 저장소 2026-09-29 갱신; projects.blender.org 스타 28; Blender 5.1+ 필요 | blender.org는 이것이 LLM이 생성한 코드를 안전장치 없이 실행한다고 경고한다. 도구 목록은 자세히 검사하지 않았다. | https://projects.blender.org/lab/blender_mcp |
| Grease Pencil v3 Line Art 모디파이어 + SVG/PDF 익스포터(Blender 코어) | 플랫 렌더(선화) / 벡터 내보내기 | Line Art는 메시에서 가림이 올바른 윤곽선, crease, edge-mark, 교차선, light-contour, 그림자 선을 GP 스트로크로 계산한다. wm.grease_pencil_export_svg/pdf가 스트로크를 쓴다(use_fill, stroke_sample, use_uniform_width, use_clip_camera). 5.1에서 구멍 있는 채우기, 5.2에서 Line Art 'Fill Strokes', Delaunay 채우기 솔버, 코너 유형 내보내기가 추가됐다. | 3 | GPL-2.0-or-later | 예 | 활발(5.2 릴리스 노트) | 헤드리스 시험: Line Art는 스트로크 68개를 정상 평가했지만, blender -b에서 GP SVG 내보내기는 퇴화한 좌표(viewBox 높이 0, y 약 -4e6)를 썼다. 카메라 뷰 뷰포트가 있는 GUI 세션에서 내보내거나, 평가된 스트로크 위치를 읽어 직접 투영할 것. Line Art 스트로크는 열린 체인이라 'Fill Strokes'로는 영역 채우기를 얻을 수 없다. | https://developer.blender.org/docs/release_notes/5.2/grease_pencil/ |
| Workbench 플랫 렌더(AA 끔) → 정확한 팔레트 VTracer(폴백 래스터 경로) | 플랫 렌더 → 벡터화 | Workbench(Flat, Attribute 색, render_aa OFF, Standard 뷰 변환, dither 0)로 면별 톤 속성을 렌더해 모든 픽셀을 정확한 팔레트 색으로 만든다. 그다음 VTracer 1.0.0-alpha.4 polygon 모드에서 --palette-file, --hierarchical cutout 또는 stacked, 작은 --filter-speckle로 트레이싱한다. | 3 | MIT | 예 | ★7,322; 2026-10-17 푸시; 릴리스 1.0.0-alpha.4(2026-08-29) | 2–4배로 렌더하고 이후에 단순화한다. cutout 모드는 이음매를 피하려면 overdraw 스트로크가 필요하다. 203X식 선명함에는 여전히 정확한 투영이 우월하다. | https://github.com/visioncortex/vtracer |
| mapshaper(위상 보존 단순화, SVG 내보내기) | 벡터화(라벨 래스터 폴리곤화 → 공유 호 단순화) | 공유 호(TopoJSON식 위상) 위에서 폴리곤 레이어를 단순화하므로 이웃이 틈 없이 유지되고, SVG로 내보낸다. 오브젝트 ID나 톤 라벨 렌더에 OpenCV findContours 또는 GDAL polygonize와 함께 쓴다. | 3 | MPL-2.0 | 예 | v0.7.88 2026-10-17 릴리스; ★4,191 | 여기서 스모크 테스트하지 않았다. 먼저 폴리곤화 단계가 필요하며, OpenCV는 시스템 Python에 있다. | https://github.com/mbloch/mapshaper |
| Scene To SVG(Craszh/BlenderModelToSVG) | 벡터 저작(3D→SVG 애드온) | 메시, 커브, GP, 폰트 오브젝트를 뷰포트나 카메라 오브젝트를 통해 SVG로 내보내는 Blender 애드온. 충돌 폴리곤의 BSP 트리 절단, 깊이 정렬 휴리스틱, 점·평면 광원 셰이딩, 후면 컬링, 머티리얼별 채우기·스트로크·패턴·이미지 스타일, CSS 애니메이션을 제공한다. | 3 | GPL-3.0 | 예 | ★9; 마지막 푸시 2023-04-15; Blender 3.2용으로 테스트됨 | 5.2.2 헤드리스 시험 실패: 카메라 오브젝트가 있어도 `AttributeError: 'NoneType' object has no attribute 'region_3d'`. 같은 톤 면을 병합하지 않아 패스 수가 많게 유지된다. | https://github.com/Craszh/BlenderModelToSVG |
| three.js SVGRenderer(addons/renderers/SVGRenderer.js) | 벡터 저작(JS 3D→SVG) | 화가 정렬(Projector)로 장면을 삼각형별로 SVG 패스에 투영한다. 광원과 함께 Basic, Lambert, Phong, Standard, Normal 머티리얼, 이음매를 가리는 0.5 px 'overdraw', setQuality와 정밀도 제어를 지원한다. | 3 | MIT | 예 | three.js r186(2026-09-24); ★116k; 2026-10-17 푸시 | 출력이 삼각형 단위라 Shapely나 Clipper 병합 단계가 필요하다. 삼각형별 중심점 정렬은 이 레인 시험에서 본 큰 면 실패를 똑같이 겪는다. 스모크 테스트하지 않았다. npm 패키지가 약 30 MB다. | https://github.com/mrdoob/three.js/blob/dev/examples/jsm/renderers/SVGRenderer.js |
| @elchininet/isometric(TypeScript 아이소메트릭 SVG 라이브러리) | 벡터 저작(코드 우선 아이소 SVG) | SVG로 직접 아이소메트릭 투영을 만든다: 아이소 축 위의 평면, 사각형, 원, 패스, 텍스트, 그룹. | 3 | Apache-2.0 | 예 | v4.0.0(2026-03-29); 2026-10-11 푸시; ★242 | 지오메트리를 손으로 코딩하므로 콜로세움 같은 복잡한 랜드마크에는 맞지 않는다. 스모크 테스트하지 않았다. | https://github.com/elchininet/isometric |
| Kenney 3D 키트(Pirate Kit, Castle Kit, Mini Characters) | 에셋(저폴리 키트) | Pirate Kit(에셋 70개: 배, 부두, 요새 벽), Castle Kit(75개: 벽, 탑, 공성 병기, 캐릭터), Mini Characters(작은 사람 25명). 모두 CC0. | 3 | CC0 1.0 | 예 | 운영 중(kenney.nl 페이지 2026-10-18 접속 가능) | 배와 병사는 로마 고증에 맞지 않아 실루엣을 다시 모델링해야 한다. 키트 내용은 페이지와 미러의 설명에서 가져왔다. | https://kenney.nl/assets/pirate-kit |
| Quaternius 팩(Ultimate Modular Ruins, Medieval Village MegaKit, Pirate Kit) | 에셋(저폴리 키트) | 무료 CC0 저폴리 팩. Ruins는 폼페이·포룸 맥락용 기둥과 아치, 마을 키트는 비계 같은 목재와 소품, Pirate Kit는 포르투스용 배를 준다. | 3 | CC0(팩 페이지에 명시) | 예 | 운영 중 | 팩 내용을 개별 검사하지 않았다. 로마 전용 팩은 찾지 못했다. | https://quaternius.com/packs/ultimatemodularruins.html |
| Freestyle SVG Exporter(확장) | 플랫 렌더(선화) → SVG | Freestyle 스트로크를 SVG로 쓰며, 라인셋마다 Inkscape 레이어 하나를 만든다. 'Fill Contours'는 각 오브젝트의 외곽 윤곽에서 evenodd 채우기 패스를 만들고 머티리얼 diffuse로 색칠한다. | 2 | GPL-2.0-or-later | 예 | v1.0.0 2024-05-14 공개, 'offered as is, with limited support' | Freestyle은 점 단위로 스트로크 스타일을 주고 SVG는 패스 단위로 주므로, 출력은 손실 있는 근사다. | https://extensions.blender.org/add-ons/freestyle-svg-exporter/ |
| Vector Render(mrossini-ethz/vector-render) | 벡터 저작(3D→SVG 애드온) | 카메라 뷰를 SVG나 MetaPost로 내보낸다: 머티리얼 색으로 칠한 메시 면, 선 램프(sun lamp) 셰이딩, 숨은 선·점선 엣지, 3D 위치 텍스트 라벨. | 2 | GPL-2.0 | 예 | ★28; 마지막 푸시 2021-10-09 | Blender 5.x에서 시험되지 않았다. | https://github.com/mrossini-ethz/vector-render |
| FreeCAD BIM ArchVRM / TechDraw ArchView 'Solid' 모드 | 벡터 저작(CAD 투영) | ArchVRM('Arch Vector Rendering Module')은 투영된 도형을 채워진 면으로 SVG 렌더링한다. 면 정렬·비교, 은면 제거, 단면 절단을 하며 TechDraw에서 Arch 뷰의 'Solid' 모드에 쓰인다. TechDraw 자체는 은선 처리된 아이소메트릭 선 뷰를 준다. | 2 | LGPL-2.1 | 예 | FreeCAD 1.1.4(2026-09-28); ★34k | FreeCAD 다운로드가 약 1 GB인데 여유 디스크는 약 9 GiB다. 위키가 봇 차단되어 기능은 ArchVRM 소스 docstring에서 가져왔다. | https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/BIM/ArchVRM.py |
| Zdog(캔버스·SVG용 플랫 의사 3D 엔진) | 벡터 저작(작은 소품·인물) | 2D 캔버스나 SVG API로 렌더하는 평평하고 둥근, 디자이너 친화적 의사 3D 도형. | 2 | MIT(README) | 예 | v1.1.1(2019-10-23); 마지막 푸시 2023-07-18; 휴면 | 엄격한 아이소 면이 아니라 둥근 '디자이너' 룩이다. | https://github.com/metafizzy/zdog |
| fogleman/ln(3D 선화 엔진) | 플랫 렌더(은선 제거 선화) | 3D 장면을 은선이 제거된 벡터 선화(SVG/PNG)로 렌더하는 Go 라이브러리. | 2 | MIT | 예 | ★3,471; 마지막 푸시 2019-07-19 | 선만 그린다. Go 툴체인이 필요하다. | https://github.com/fogleman/ln |
| arjun988/blender-skills(isometric-style, vector-style, stylized-style 스킬) | 에이전트 스킬 | Claude Code, Cursor, Codex용 Blender 에이전트 스킬 94개. isometric-style은 54.736° 직교 카메라, 세트당 고정 각도, 타일 풋프린트를 다룬다. vector-style은 'hard color regions, no noisy textures'를 말한다. NPR 노트는 2–3단계 ColorRamp를 쓴 Shader-to-RGB를 다룬다. | 2 | MIT | 예 | ★342; 2026-07-10 푸시 | 스킬로 추가해야 한다. 이 레인의 스크립트 대비 추가 가치가 낮다. | https://github.com/arjun988/blender-skills |
| Isometric Scene Setup(Blender 확장) | 모델링 / 카메라 설정 | 게임용 아이소메트릭 장면 설정과 2D 뷰 공간 노멀 렌더링. | 2 | GPL-3.0-or-later / MIT | 예 | v1.0.1(2026-03-04) | 페이지에 정확한 각도가 명시되지 않았다. 시험하지 않았다. | https://extensions.blender.org/add-ons/isometric-scene-setup/ |
| Section Toolbox(Blender 확장) | 모델링(컷어웨이) / 내보내기 | SVG/DXF 내보내기가 있는 파라메트릭 단면 상자와 평면 절단(태그라인 기준). | 2 | GPL-3.0-or-later | 예 | v0.0.2(인덱스 항목; 최소 Blender 4.2) | 확장 인덱스의 태그라인만 확인했다. SVG 출력 품질은 알 수 없다. | https://extensions.blender.org/add-ons/stb-section-toolbox/ |
| Poly Haven 모델 | 에셋 | CC0 모델 521개 카탈로그(API 확인). 관련 항목: 도자기 항아리·꽃병(암포라 대용), 통, 상자, 사다리, 모듈식 목재 부두, 네덜란드 배(시대착오). | 2 | CC0 | 예 | 운영 중(api.polyhaven.com) | 로마 랜드마크는 없다. | https://polyhaven.com/models |
| Export Curve as SVG(Blender 확장) | 벡터 내보내기(커브·와이어프레임) | 커브, 텍스트, 메시 엣지를 위·앞·옆, 현재 뷰, 카메라에서 SVG 패스로 내보내며 채우기와 스트로크를 설정할 수 있다. | 1 | GPL-3.0-or-later | 예 | v2.0.0; Blender 5.0+ 필요; 저장소 github.com/GilbertoRodrigues/export_curve_as_svg | 페이지 날짜가 일관되지 않다(2025-12-07 공개, 'What's New' 날짜 2026-10-06). | https://extensions.blender.org/add-ons/export-curve-as-svg/ |
| dogukanaslan0/svgexporter | 벡터 내보내기 | 메시와 커브 오브젝트를 위·앞·옆·아이소 뷰나 카메라에서 근거리/원거리 클리핑과 자동 스케일로 SVG로 내보낸다. | 1 | MIT | 예 | ★1; 2025-09-09 푸시 | 매우 작은 프로젝트. 시험하지 않았다. | https://github.com/dogukanaslan0/svgexporter |
| Smithsonian Open Access 3D | 에셋 | 3D 스캔을 포함한 Smithsonian CC0 오픈 액세스 컬렉션. | 1 | CC0(Smithsonian Open Access 정책) | 예 | 운영 중 | 3d.si.edu와 si.edu/openaccess 모두 이 레인의 요청에 403을 반환해, 이번 세션에서 라이선스와 내용을 확인하지 못했다. | https://3d.si.edu/ |
| Open Heritage 3D(CyArk), 폼페이 포함 | 에셋(LiDAR·포토그래메트리) | 문화유산 현장의 LiDAR·포토그래메트리 데이터셋. 폼페이는 초기 현장 중 하나다. | 1 | 데이터셋별 Creative Commons, 대부분 CC BY-NC | 아니요 | 사이트 접속 가능(2026-10-18) | 폼페이 데이터셋의 구체적 라이선스는 확인하지 않았다. | https://openheritage3d.org/ |

### D-5-2. 후보별 보충 정보 (적합 이유 · 로컬 설치 · 에이전트 구동 · 분류 · 근거 URL)

1. **커스텀 bpy 면 투영 + Shapely HSR/병합 스크립트** (분류: 3D→벡터 파이프라인)
   - 적합 이유: 203X식 출력으로 가는 직접 경로다. 정확한 아이소 축, 선명한 엣지, 면당 적은 톤, 적은 패스, Figma에 맞는 그룹을 준다. 면 420개가 올바른 가림으로 17패스가 됐다. 완전히 헤드리스이며 Bash나 Blender MCP로 스크립트 구동할 수 있다.
   - 로컬 설치: 예(Blender 5.2.2 LTS + 시스템 Python 3.14 Shapely 2.1.2, numpy)
   - 에이전트 구동: CLI(`blender -b --python`) / Blender MCP execute_blender_code
   - 근거: https://shapely.readthedocs.io/en/stable/reference/shapely.union_all.html, https://docs.blender.org/api/current/bpy_extras.object_utils.html
2. **Blender 5.2 LTS** (분류: 3D DCC)
   - 적합 이유: 지오메트리의 뼈대다. 올바른 아이소 지오메트리와 랜드마크별로 큐레이션한 크기가 203X 포스터가 보여주는 것이다. 이미 설치돼 있고 MCP로 구동할 수 있다.
   - 로컬 설치: 예: `/opt/homebrew/bin/blender` -> 5.2.2 LTS
   - 에이전트 구동: CLI(`-b --python`), Python API, Blender MCP
   - 근거: https://developer.blender.org/docs/release_notes/5.2/grease_pencil/, https://www.blender3darchitect.com/architectural-visualization/create-true-isometric-camera-architecture/, https://wiki.blender.jp/Extensions:2.6/Py/Scripts/Add_Mesh/Create_IsoCam
3. **Shapely 2.x(GEOS)** (분류: 지오메트리 라이브러리)
   - 적합 이유: 독립 트레이싱이 만드는 슬리버와 틈을 없애고, 최소한의 깨끗한 패스를 낸다.
   - 로컬 설치: 예(시스템 python3, 2.1.2). Blender 번들 Python 안에는 없음
   - 에이전트 구동: Python 스크립팅
   - 근거: https://shapely.readthedocs.io/en/stable/reference/shapely.union_all.html
4. **MCP for Blender(ahujasid/mcp-for-blender)** (분류: MCP)
   - 적합 이유: 에이전트가 랜드마크를 만들고, 실행 중인 GUI에서 투영 스크립트를 돌리고(Scene To SVG나 GP SVG 내보내기처럼 뷰포트에 의존하는 익스포터도 쓸 수 있게 된다), 결과를 시각적으로 확인할 수 있다.
   - 로컬 설치: 예: `~/Library/Application Support/Blender/5.2/scripts/addons/blender_mcp.py`(bl_info version 1.8)
   - 에이전트 구동: MCP
   - 근거: https://github.com/ahujasid/mcp-for-blender, https://pypi.org/project/mcp-for-blender/
5. **Sketchfab** (분류: 에셋 라이브러리)
   - 적합 이유: 콜로세움, 수도교, 크레인의 비례가 맞는 블록아웃을 가장 빨리 얻을 수 있는 출처다. 저폴리 항목은 깨끗하게 투영된다.
   - 로컬 설치: 아니요(Blender MCP import_asset으로 가져올 수 있음)
   - 에이전트 구동: API / Blender MCP search_assets + import_asset
   - 근거: https://api.sketchfab.com/v3/search?type=models&downloadable=true&q=colosseum, https://sketchfab.com/models/c3c5157559344c74b2c0bacc89036692
6. **Poly Pizza** (분류: 에셋 라이브러리)
   - 적합 이유: 저폴리 평면이 적은 톤의 벡터로 깨끗하게 투영된다. 203X의 '작은 인부' 밀도에 맞는 인물과 소품에 좋다.
   - 로컬 설치: 아니요(Blender MCP import_asset이 Poly Pizza를 지원)
   - 에이전트 구동: Blender MCP / 웹
   - 근거: https://poly.pizza/m/83ftBPyiSf, https://poly.pizza/m/cvCqP8aHvn5, https://poly.pizza/search/roman
7. **Blender Lab 공식 MCP 서버** (분류: MCP)
   - 적합 이유: 커뮤니티 서버의 공식 대안이지만, 이미 연결된 서버와 기능이 겹치고 에셋·벡터 기능이 없다.
   - 로컬 설치: 아니요
   - 에이전트 구동: MCP
   - 근거: https://www.blender.org/lab/mcp-server/, https://projects.blender.org/lab/blender_mcp
8. **Grease Pencil v3 Line Art + SVG/PDF 익스포터** (분류: Blender 코어)
   - 적합 이유: 투영 채우기 위에 얹는 선명한 외곽선·이음선(석재 블록 줄, 아치 테두리, 균열선)에 좋다. 그 자체로는 면별 3톤 채우기를 만들 수 없다.
   - 로컬 설치: 예(5.2.2에 연산자와 LINEART 모디파이어가 있음)
   - 에이전트 구동: Python API. 헤드리스 내보내기는 신뢰할 수 없음
   - 근거: https://developer.blender.org/docs/release_notes/5.2/grease_pencil/, https://developer.blender.org/docs/release_notes/5.1/grease_pencil/, https://docs.blender.org/manual/en/dev/files/import_export/grease_pencil_svg.html
9. **Workbench 플랫 렌더 → 정확한 팔레트 VTracer** (분류: 벡터라이저)
   - 적합 이유: 지오메트리를 투영할 수 없을 때(스캔, 과도한 불리언, AI 메시) 쓴다. 시험 장면에서 회화풍 경로(사용자가 폐기한 이전 작업)의 약 19k 패스 대신 깨끗한 18패스를 냈다. 다만 엣지가 픽셀 단위로 양자화되어 곡선에 계단식 흔들림이 있고, 경계를 공유하지 않는다.
   - 로컬 설치: 예: `/Users/um-yunsang/roman-concrete-private-refs/.tools/vtracer/vtracer`(1.0.0-alpha.4)
   - 에이전트 구동: CLI
   - 근거: https://github.com/visioncortex/vtracer/releases
10. **mapshaper** (분류: 벡터 정리)
    - 적합 이유: 래스터 폴백에서 VTracer를 대신하는 공유 위상 방식이다. 맞닿은 영역 사이의 슬리버와 틈을 피한다.
    - 로컬 설치: 아니요(`bunx mapshaper`로 실행)
    - 에이전트 구동: CLI
    - 근거: https://github.com/mbloch/mapshaper
11. **Scene To SVG(Craszh/BlenderModelToSVG)** (분류: Blender 애드온)
    - 적합 이유: 커스텀 스크립트에 가장 가까운 기성 애드온(BSP + 조명 + 채우기)이다. 비교하거나 기법을 빌려 오는 데 유용하다.
    - 로컬 설치: 아니요(스크립트만 scratchpad에 내려받음)
    - 에이전트 구동: 실제로는 GUI 전용. Python 연산자 object.export_svg는 3D 뷰포트가 필요하다.
    - 근거: https://github.com/Craszh/BlenderModelToSVG
12. **three.js SVGRenderer** (분류: JS 3D 라이브러리)
    - 적합 이유: Bun/JS 경로다. Blender에서 내보낸 glTF를 three.js OrthographicCamera로 보고 SVG로 만든다. 브라우저나 헤드리스 Chrome에서 빠르게 반복할 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 스크립팅 API(DOM 필요: 브라우저, 헤드리스 Chrome 또는 DOM shim)
    - 근거: https://github.com/mrdoob/three.js/blob/dev/examples/jsm/renderers/SVGRenderer.js, https://github.com/mrdoob/three.js/releases
13. **@elchininet/isometric** (분류: JS 아이소 라이브러리)
    - 적합 이유: 지그재그 공정 플랫폼, 바닥 슬래브, 정보 패널 타일, 신문 포스터 더미 같은 단순 소품을 3D 단계 없이 정확한 아이소 축으로 그린다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 스크립팅 API(bun)
    - 근거: https://github.com/elchininet/isometric
14. **Kenney 3D 키트** (분류: 에셋 라이브러리)
    - 적합 이유: 투박한 저폴리 지오메트리가 플랫 아이소 벡터에 잘 맞는다. 배, 부두, 공성 기계는 재스타일하면 포르투스의 배, 크레인, 인부로 개조할 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 다운로드 + Blender 가져오기(glTF/FBX/OBJ)
    - 근거: https://kenney.nl/assets/pirate-kit, https://kenney.nl/assets/castle-kit, https://kenney.nl/assets/mini-characters, https://opengameart.org/content/castle-kit
15. **Quaternius 팩** (분류: 에셋 라이브러리)
    - 적합 이유: 깨끗한 저폴리 CC0 부품이 투영 파이프라인에 맞는다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 다운로드 + Blender 가져오기
    - 근거: https://quaternius.com/packs/ultimatemodularruins.html, https://quaternius.com/packs/medievalvillagemegakit.html, https://quaternius.com/packs/piratekit.html
16. **Freestyle SVG Exporter(확장)** (분류: Blender 확장)
    - 적합 이유: 외곽선에는 괜찮지만 채우기가 오브젝트당 평면 실루엣 하나뿐이고 면별 3톤이 없다. 채우기는 불안정하다고 문서화돼 있다.
    - 로컬 설치: 아니요(4.2 이후 번들되지 않음. zip을 scratchpad에서 검사했고 sha256이 인덱스와 일치)
    - 에이전트 구동: Python(렌더 핸들러)
    - 근거: https://extensions.blender.org/add-ons/freestyle-svg-exporter/, https://docs.blender.org/manual/en/4.1/addons/render/render_freestyle_svg.html, https://github.com/folkertdev/freestyle-svg-exporter
17. **Vector Render(mrossini-ethz/vector-render)** (분류: Blender 애드온)
    - 적합 이유: 개념은 맞지만 오래됐고, 교차하는 폴리곤을 처리할 수 없다고 명시돼 있다. 부드러운 셰이딩도, 드리운 그림자도 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: GUI 애드온
    - 근거: https://github.com/mrossini-ethz/vector-render
18. **FreeCAD BIM ArchVRM / TechDraw ArchView 'Solid' 모드** (분류: CAD)
    - 적합 이유: 면 정렬 채우기 SVG 접근이 통한다는 것을 보여주지만, 일러스트 작업에 무거운 CAD 설치를 끌어들인다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python 콘솔 / FreeCADCmd
    - 근거: https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/BIM/ArchVRM.py, https://github.com/FreeCAD/FreeCAD/releases
19. **Zdog** (분류: JS 의사 3D)
    - 적합 이유: 플랫 스타일의 작은 인부, 암포라, 아이콘에는 쓸 수 있지만 건축 규모로는 확장되지 않는다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 스크립팅 API
    - 근거: https://github.com/metafizzy/zdog
20. **fogleman/ln** (분류: 선 렌더러)
    - 적합 이유: 기술적 단면 레이어용 깨끗한 선화를 주지만 채우기는 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Go API
    - 근거: https://github.com/fogleman/ln
21. **arjun988/blender-skills** (분류: 에이전트 스킬)
    - 적합 이유: 지침은 정확하지만 얇다. 벡터 내보내기 파이프라인은 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 스킬(`npx skills add ... --skill isometric-style`)
    - 근거: https://skills.sh/arjun988/blender-skills/isometric-style, https://github.com/arjun988/blender-skills
22. **Isometric Scene Setup(Blender 확장)** (분류: Blender 확장)
    - 적합 이유: 뷰 공간 노멀 패스로 래스터 폴백의 정확한 톤 라벨을 만들 수 있다. 카메라 설정은 어차피 스크립트로 간단히 할 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: GUI 애드온 / Python
    - 근거: https://extensions.blender.org/add-ons/isometric-scene-setup/
23. **Section Toolbox(Blender 확장)** (분류: Blender 확장)
    - 적합 이유: 콜로세움 기초 컷어웨이와 균열 치유 단면 외곽선에 쓸모가 있을 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: GUI 애드온
    - 근거: https://extensions.blender.org/add-ons/stb-section-toolbox/
24. **Poly Haven 모델** (분류: 에셋 라이브러리)
    - 적합 이유: 대부분 조밀한 메시의 실사 스캔 소품이라 플랫 투영에 이상적이지 않다. 참조용이나 소품 몇 개에는 괜찮다.
    - 로컬 설치: 아니요(Blender MCP가 지원)
    - 에이전트 구동: API / Blender MCP
    - 근거: https://api.polyhaven.com/assets?t=models
25. **Export Curve as SVG(Blender 확장)** (분류: Blender 확장)
    - 적합 이유: 메시는 엣지 와이어프레임으로 나가며, 면 투영이나 깊이 정렬이 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: GUI 애드온
    - 근거: https://extensions.blender.org/add-ons/export-curve-as-svg/
26. **dogukanaslan0/svgexporter** (분류: Blender 애드온)
    - 적합 이유: 셰이딩이나 은면 제거가 문서화되지 않은 단순한 선 익스포터다.
    - 로컬 설치: 아니요
    - 에이전트 구동: GUI 애드온
    - 근거: https://github.com/dogukanaslan0/svgexporter
27. **Smithsonian Open Access 3D** (분류: 에셋 라이브러리)
    - 적합 이유: 로마 건축과 관련성이 낮고, 스캔 토폴로지는 플랫 벡터에 맞지 않는다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 웹/API(키 필요)
    - 근거: https://3d.si.edu/
28. **Open Heritage 3D(CyArk)** (분류: 에셋 라이브러리)
    - 적합 이유: 대부분 비상업 라이선스인 포인트 클라우드와 조밀한 메시다. 배치 참조로만 유용하다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 웹(등록 필요)
    - 근거: https://openheritage3d.org/, https://cyark.org/about/openheritage

---

# 제2부. 레인 E: 플랫 아이소메트릭 벡터 아트를 위한 OSS AI 생성·벡터화, 그리고 노이즈 없는 깨끗한 벡터를 얻는 법

## E-1. 한눈에 보는 결론

- 노이즈는 VTracer 설정이 아니라 **트레이서에 들어가는 입력**에서 나온다. 회화풍 입력은 어떤 설정이나 후처리로도 203X식 플랫 면에 닿지 못했다(사용자가 폐기한 이전 작업인 r23 Pompeii 크롭: 기본값 3,343패스 → 강한 정리 후 312패스지만 형태가 녹아내림).
- 해법은 지오메트리 우선이다. AA OFF + dither 0 Blender 플랫 렌더(정확히 43색) → VTracer 1.0.0-alpha.4 stacked·polygon·고정 팔레트로 44패스, 구멍 0, RMSE 1.35%를 얻었다.
- 밝은 점의 재현된 원인은 Blender 기본 dither(픽셀 26% 변동, 단색 마스크 53% 손실, 핀홀 65k개 초과), VTracer cutout 모드의 구멍(2,952 px)과 이음매, 맞닿은 도형의 AA 이음매다.
- 2026년 OSS image-to-SVG·text-to-SVG 모델은 A2 일러스트 장면에 쓸 수 없다. 생성 AI는 Blender 자체 패스로 지오메트리를 고정한 ControlNet 기반의 선택적 디테일 단계로만, 그리고 Apache-2.0 모델로만 쓴다.
- 203X 포스터는 IP-Adapter·Redux·LoRA 학습·트레이싱의 입력으로 쓰지 말고, 사람이 분석하는 용도로만 쓴다.

## E-2. 핵심 발견

1. **노이즈는 VTracer 설정이 아니라 트레이서에 들어가는 입력에서 나온다.** 벡터 영역 하나에는 한 가지 색으로 된 평평한 영역이 필요한데, 회화풍이나 텍스처 있는 렌더에는 그런 영역이 없다. 사용자가 폐기한 이전 작업인 r23 Pompeii 장면의 1000x800 크롭으로 측정했다. VTracer 기본값은 패스 3,343개, 고유 채우기 3,277개를 냈다. 세밀한 설정(-f 2 -p 8 -g 8)은 5,183패스를 냈다. 강한 정리(mean-shift + kuwahara + 18색 리맵 + cutout + simplify)는 312패스·18채우기까지 줄였지만 형태가 녹아내렸다. 바구니, 기와, 인물이 덩어리로 합쳐졌다(비교 이미지: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/vec-lane/cmp_zoom.png`). 그런 입력을 203X식 플랫 면으로 바꿔 주는 트레이서 설정은 없다. 면은 트레이싱하기 전에 이미 평평해야 한다.

2. **'밝은 점 / 밝은 반점'의 원인 세 가지를 재현했다.**
   - (1) **Blender 기본 렌더 디더**(scene.render.dither_intensity = 1.0, 헤드리스로 확인)가 픽셀의 26%를 한 단계씩 옮긴다. 플랫 시험 장면의 고유색이 43개에서 222개로 늘었다. 정확히 한 색을 고르는 마스크는 픽셀의 53%를 잃고(532k → 252k) 65k개가 넘는 핀홀로 쪼개졌다. 그래서 VectorCraft(사용자가 폐기한 이전 작업)나 스크립트의 색별 마스크 단계는 이것을 규칙적인 점 격자로 바꾼다(`/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/vec-lane/mask_zoom_dither.png`).
   - (2) **VTracer 1.0.0-alpha.4의 --hierarchical cutout**은 -f 0에서도 얇은 물/벽돌 띠를 빠뜨리고 투명 구멍 2,952 px을 남겼다. stacked 모드는 0이었다.
   - (3) **가장자리끼리만 맞닿은 도형**은 얇은 안티앨리어싱 이음매('conflation artifacts')를 보인다. 마젠타 배경 위 cutout 출력에서 분홍 선으로 보였다(zoom3.png).
   - 재현하지는 않았지만 그럴듯한 추가 원인: filter_speckle을 통과하는 텍스처 속 밝은 반사광 점, AI 이미지 디코더와 업스케일러가 남기는 주기적 격자 패턴.

3. **해상도는 넘을 수 없는 상한이다.** 원본 래스터는 1254-1536 px이다(pompeii 1448x1086, colosseum 1536x1024, pantheon/aqueduct 1254x1254). A2 300 dpi는 4961x7016 px다. 300 dpi에서 r23(사용자가 폐기한 이전 작업)의 콜로세움 크롭은 눈에 띄게 흐리고, 작은 인부들은 원본에서 키가 약 30-50 px이다. 트레이싱은 픽셀에 없는 엣지를 더할 수 없다. 각 오브젝트를 최종 인쇄 픽셀 크기의 2배 이상으로 따로 렌더하거나 생성한다.

4. **지오메트리 우선 경로는 통한다.** Blender에서 Workbench, STUDIO 조명, 플랫 면, render_aa OFF, dither 0으로 시험 장면을 헤드리스 렌더하자 정확히 43색이 나왔다. `VTracer --hierarchical stacked --mode polygon -p 8 -g 0 --palette-file`로 트레이싱하니 44패스, 37채우기, 구멍 0, RMSE 1.35%였고, 선명한 아이소 엣지와 203X처럼 보이는 패싯 원통이 나왔다. --simplify 1.0을 더하면 세그먼트 수가 대략 절반(843 → 463)이 되고 RMSE는 1.76%다. spline 모드 기본값은 상자형 건축의 모서리를 둥글리므로, 건물에는 polygon 모드를 쓴다.

5. **VTracer 1.0.0-alpha.4**(로컬 바이너리, 2026-08-29 릴리스, 저장소 2026-10-17 푸시)는 여기서 중요한 기능을 더한다: --palette / --palette-file(OKLab에서 가장 가까운 팔레트 색으로 스냅), --max-colors, --simplify, --clustering watershed, 이음매 없는 cutout 모드. PyPI 안정판은 여전히 0.6.15이고 1.0.0a4는 프리릴리스다. ComfyUI-ToSVG의 requirements.txt는 그냥 'vtracer'라고만 적어서 0.6.15가 설치되므로 이 기능들이 전혀 없다. 고정 팔레트를 쓸 때는 -p 8 -g 0으로 설정한다. 그렇지 않으면 기본 클러스터링이 이웃 패싯 톤을 병합한다(시험에서 37개 대신 25개 채우기).

6. **2026년 기준 OSS image-to-SVG·text-to-SVG 모델은 A2 일러스트 장면에 쓸 수 없다.** StarVector의 README는 'will not work for natural images or illustrations'(자연 이미지나 일러스트에는 동작하지 않는다)라고 한다. VTracer 대비 SVG-Bench 우위는 아이콘, 폰트, 다이어그램에서만 나온다(Icons DinoScore 0.984 vs 0.940). OmniSVG1.1-8B(Apache-2.0, 2026-03-30)는 약 26 GB의 CUDA VRAM이 필요하고 4,096 토큰에 98초가 걸리는데, 203X 수준 랜드마크 하나에는 훨씬 많은 토큰이 필요하다. LayerTracer의 공개 가중치는 아이콘·이모지 FLUX LoRA뿐이고 약 50 GB 메모리가 필요하다. LLM4SVG 가중치는 여전히 'pending'으로 표시돼 있다. Chat2SVG, LayerPeeler, SuperSVG는 라이선스 파일이 없다. DiffVG는 Apple MPS를 지원하지 않으므로(이슈 #72 열림) 이 Mac에서는 LIVE, VectorFusion, SVGDreamer, NeuralSVG도 배제된다. 2026년 WildSVG 벤치마크 논문은 최신 멀티모달 모델이 'well below what is needed for reliable SVG extraction in real scenarios'(실제 시나리오에서 신뢰할 수 있는 SVG 추출에 필요한 수준에 한참 못 미친다)라고 한다. 기껏해야 OmniSVG로 정보 패널용 작은 픽토그램 초안을 만들 수 있다.

7. **생성 AI는 선택적 디테일링·재스타일 단계로만 쓴다.** 지오메트리는 Blender 자체 패스(depth, normal, lineart, canny)로 ControlNet에 고정하며, 회화풍 이미지에서 추정하지 않는다. Comfy Cloud 카탈로그(MCP로 확인)에는 이미 controlnet-union-sdxl-1.0, Qwen-Image-InstantX-ControlNet-Union, Qwen-Image-2512-Fun-Controlnet-Union-2602와 Z-Image-Turbo Fun Union ControlNet 템플릿이 있다. 아이소메트릭 LoRA는 없으므로 가져와야 한다. Comfy Cloud에서 돌리면 9 GiB의 여유 디스크를 채우지 않아도 된다.

8. **라이선스.**
   - 다음 베이스는 Apache-2.0이라 공개 포스터에 안전하다: Qwen-Image-2512, Qwen-Image-Edit-2509/2511, Qwen-Image-Layered, Z-Image-Turbo와 alibaba-pai Fun ControlNet Union 2.1, FLUX.2-klein-4B, InstantX Qwen ControlNet Union, xinsir SDXL union, h94 IP-Adapter.
   - SDXL은 OpenRAIL++다(상업적 사용 허용, 사용 제한 있음).
   - 비상업: FLUX.1-dev, FLUX.1-Redux-dev, FLUX.1-Depth-dev, FLUX.1-Kontext-dev, FLUX.2-dev, FLUX.2-klein-9B. Shakker Union Pro 2.0 ControlNet은 dev 베이스 위의 'other'다.
   - 사용 전에 읽어야 할 커스텀 라이선스: Krea-2(커뮤니티 라이선스), Qwen-Image-2.1('other'), FLUX 3 Image Klein('flux-kommunity').
   - LoRA 자체의 라이선스 태그가 베이스 모델의 라이선스를 덮어쓰지 않는다. ISOMETRIC-REDMOND-FLUXKLEIN9B는 Apache-2.0으로 태그돼 있지만 비상업 베이스 위에 있다.
   - 대부분의 아이소메트릭·플랫 벡터 LoRA(strangerzonehf, Muapi, KappaNeuro 등)는 학습 데이터를 문서화하지 않아 출처(provenance) 위험이 있다.

9. **203X 관련 저작권 주의.** 203X 포스터를 IP-Adapter, Flux Redux, Qwen-Edit 다중 이미지 참조, LoRA 학습에 넣지 말고, 트레이싱하지도 않는다. 크롭을 보면 Street H 매거진에 크레딧된 의뢰 작업이다. 이미지 조건 생성은 특정 구도, 모티프, 캐릭터를 재현할 수 있어서, 일반적인 스타일은 보통 보호되지 않더라도 실질적 유사성 위험이 있다. 203X는 사람이 분석하는 용도로만 쓴다. 측정 가능한 규칙(면당 톤 수, 팔레트 비율, 외곽선 두께, 라벨·지시선 문법, 패널 그리드)을 적어 두고, 스타일 참조 세트는 직접 승인한 플랫 Blender 렌더로 만든다.

10. **독점 도구와의 비교(oss=false).** Vectorizer.AI는 도형 전체(원, 타원, 둥근 사각형, 호)를 피팅하고 안티앨리어싱을 처리한다. Recraft V4/V4.1 Vector(2026년 2월/5월)와 Quiver Arrow 2는 Comfy Cloud 파트너 템플릿으로 접근할 수 있다. 이들은 OSS 트레이서보다 깨끗한 아이콘·로고 수준 SVG를 주지만, 203X 규모의 아이소메트릭 장면을 만든다는 근거는 없다. 파이프라인이 아니라 품질 기준점으로 취급한다.

11. **작업 환경 메모.** 조사 도중(약 12:08) 사용자 지시로 이전 작업 폴더(`/Users/um-yunsang/roman-concrete-private-refs/artwork`, `.../.planning`)가 삭제됨(정상). 이후 docs/, .tools/, .remember/만 남았으므로, 과제에 적힌 r23 파일(사용자가 폐기한 이전 작업)과 203X 크롭은 더 이상 그 경로에 없다. 203X 원본 크롭은 현재 `docs/references/assets/203x/originals/` 에 있다. 이 레인은 거기서 아무것도 수정하지 않았다. 이 레인의 크롭과 시험 파일은 `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/vec-lane/` 아래에 있다.

## E-3. 권장 파이프라인

0. **원칙.** 회화풍 래스터는 절대 벡터화하지 않는다. 먼저 플랫 지오메트리를 만들고, 그것을 무손실로 트레이싱한다. AI는 지오메트리가 고정된 디테일에만 쓴다.
1. **지오메트리.** 각 랜드마크(콜로세움 + 기초 컷어웨이, 폼페이 야드, 판테온, 수도교 수로, 포르투스, 균열 자가치유 블록 3개)에 하드 엣지와 플랫 면을 가진 저폴리 Blender 모델을 쓴다(모델링 자체는 다른 레인이 다룬다). 각 색상(hue)에 고정 톤 세 개(위/왼쪽/오른쪽)를 주는데, Geometry.Normal로 구동하는 이미션 머티리얼이나 스펙큘러를 끈 Workbench STUDIO를 쓴다. 모든 오브젝트가 공유하는 직교 아이소 카메라(회전 54.736, 0, 45도)를 써서 축을 일관되게 유지한다.
2. **트레이싱용 렌더**(헤드리스: `blender -b -P`). 설정: `scene.display.render_aa='OFF'`(Workbench) 또는 필터 크기 0, `scene.render.dither_intensity=0`(기본값 1.0이 점 노이즈를 만든다), `view_transform='Standard'`, `film_transparent=True`. 각 오브젝트를 최종 인쇄 픽셀 크기의 2배로 렌더한다(시트 전체는 A2 300 dpi = 4961x7016). Object Index / Cryptomatte 마스크도 함께 쓴다. QA: `magick obj.png -unique-colors`가 팔레트 색 수와 같아야 한다.
3. **선택적 AI 디테일링**(Comfy Cloud, Apache-2.0 모델만). Qwen-Image-2512 + Fun ControlNet Union 또는 InstantX Union에 Blender의 정확한 깊이와 Freestyle/canny 선을 제어 이미지로 넣는다. 또는 Qwen-Image-Edit-2511로 플랫 렌더를 재스타일한다. 또는 Z-Image-Turbo + Fun ControlNet Union 2.1(+ ISOMETRIC-REDMOND-ZIMAGE LoRA)을 쓴다. 프롬프트는 flat vector, cel shading, 표면당 2-3톤, 단색, 텍스처/그라디언트/노이즈 없음, 선명한 엣지를 요구한다. 이미지 하나에 오브젝트 하나씩, 2048 px 이상으로 생성한다. 스타일 참조는 직접 승인한 플랫 렌더만 쓰며, 203X 이미지는 절대 쓰지 않는다.
4. **AI 래스터 정리**(Blender 렌더는 건너뜀). 선택적으로 Real-ESRGAN anime-6B로 2배 업스케일한다. 그다음 `magick in.png -mean-shift 7x7+8% -kuwahara 2 -dither None -remap project_palette.png -statistic Median 3x3 out.png`. 필요하면 OpenCV로 색별 형태학적 open/close를 하고, 오브젝트별 마스크에는 SAM 2를 쓴다.
5. **트레이싱**(ComfyUI-ToSVG의 0.6.15가 아니라 로컬 VTracer 1.0.0-alpha.4).
   - 건축: `vtracer -i obj.png -o obj.svg --hierarchical stacked --mode polygon -p 8 -g 0 -f 16 --palette-file project_palette.txt`(선택적으로 `--simplify 0.75`)
   - 인물과 유기적 형태: `--mode spline --simplify 1.0 --corner-threshold 60 -f 16`
   - 오브젝트 전체를 덮는 받침 채우기가 밑에 깔려 있지 않으면 `--hierarchical cutout`은 피한다(시험에서 구멍과 이음매를 남겼다).
   - 아주 매끄러운 외곽선이 필요하면 대안으로 Object-Index 마스크마다 potrace를 돌린다: `potrace -s -t 8 -a 0.8 -O 0.4`
6. **후처리.** 패스를 오브젝트별로 그룹화하고 이름을 붙이고, 약 4 px² 미만의 슬리버를 지운다. 선택적으로 Bun + paper.js 스크립트로 엣지를 아이소 각도(30/90/150도)에 스냅하고 같은 색 이웃을 병합한다. 레이어 편집성을 유지하도록 mergePaths/collapseGroups를 끈 채로 `bunx svgo`를 돌린다.
7. **오브젝트별 자동 QA.** SVG를 마젠타 위에 렌더(`rsvg-convert -b '#FF00FF'`)해 마젠타 픽셀 0개(구멍·이음매 없음)를 요구한다. 패스 수와 고유 채우기 수를 센다(채우기는 팔레트 크기 이하). 플랫 렌더 대비 RMSE를 확인하고(2% 이하 목표), 패스 수가 오브젝트별 예산 안에 있는지 확인한다.
8. **Figma 조립.** SVG 가져오기로 일러스트 레이어를 넣고, 그 위에 지시선·라벨·정보 패널을 Figma 네이티브 벡터와 텍스트로 만든다(타이포그래피와 차트는 다른 레인). 최종본은 A2용 PDF/X로 내보낸다.
9. **픽토그램.** OmniSVG 1.1, Recraft, Quiver는 원할 경우 정보 패널용 작은 픽토그램 초안에만 쓴다. 랜드마크에는 쓰지 않는다.

## E-4. 실제로 실행한 검증·시험과 결과

### E-4-1. 노이즈 원인 실험 수치 종합

| 실험 | 조건 | 결과 |
|---|---|---|
| 회화풍 입력 트레이싱 | r23 Pompeii 300 dpi 1000x800 크롭(사용자가 폐기한 이전 작업), `vtracer -i src.png -o A_default.svg` | 3,343패스 / 고유 채우기 3,277 / 1.4 MB |
| 〃 | `-f 2 -p 8 -g 8` | 5,183패스 / 1.8 MB |
| 〃 | 원본 크롭에 `--hierarchical cutout -f 24 --simplify 1.5 --palette-file <18 k-means colours>` | 346패스 / 18채우기 |
| 〃 | `magick -mean-shift 7x7+8% -kuwahara 2 ... -remap palette` 후 같은 트레이싱 | 312패스 / 18채우기 / 156 KB. 오브젝트가 덩어리로 합쳐짐 |
| AA·디더 조합별 고유색 | 헤드리스 플랫 아이소 시험 장면(Workbench STUDIO, 플랫 면, 직교 54.736/0/45) | AA OFF + dither 0: 43 / AA OFF + 기본 dither: 222 / AA 8 + dither 0: 944 / AA 8 + 기본 dither: 1,564 |
| 디더 기본값 확인 | `blender --factory-startup --python-expr` | dither_intensity 기본값 = 1.0 |
| 디더로 바뀐 픽셀 | `magick compare -metric AE` | 375,494 px(26%)가 최대 1/255 차이 |
| 단색 마스크 손실 | 주 회색 면의 정확한 색 마스크 | 532,487 px → 252,201 px. 디더된 마스크의 connected-components는 'too many objects'로 실패(핀홀 65k개 초과) |
| vtracer 자체 클러스터링 | `-f 0 -p 8 -g 0` | 56 대 55패스(디더를 대부분 흡수). 점 패턴은 색별 마스크 파이프라인과 팔레트 추출에 타격 |
| stacked + polygon + 팔레트 | 디더 없는 플랫 렌더, `-p 8 -g 0`, rsvg-convert로 #FF00FF 위에 렌더 | 44패스, 37채우기, 구멍 0 px, RMSE 1.35% |
| stacked + spline + `--simplify 1.0` | 〃 | 44패스, 세그먼트 463(대 843), 구멍 0, RMSE 1.76% |
| cutout + polygon | 팔레트 유무 무관, -f 0/1/2/4 모두 동일 | 구멍 2,952 px + 공유 엣지에 분홍 헤어라인 이음매 |
| 기본 spline(F1) | 〃 | 구멍 0, 상자 모서리가 둥글어짐 |
| 고정 팔레트 + 기본 클러스터링 | -p 8 -g 0을 설정하지 않음 | 채우기 37개 대신 25개(이웃 패싯 톤 병합) |
| 해상도 | 원본 래스터 vs A2 300 dpi | 1448x1086(pompeii), 1536x1024(colosseum), 1254x1254(pantheon, aqueduct) vs 4961x7016. 인부는 원본에서 약 30-50 px |

### E-4-2. 전체 시험 기록

1. **회화풍 입력**(사용자가 폐기한 이전 작업인 r23 Pompeii의 300 dpi 1000x800 크롭). `vtracer -i src.png -o A_default.svg`는 3,343패스 / 고유 채우기 3,277 / 1.4 MB. `-f 2 -p 8 -g 8`은 5,183패스 / 1.8 MB. 원본 크롭에 `--hierarchical cutout -f 24 --simplify 1.5 --palette-file <18 k-means colours>`는 346패스 / 18채우기. `magick -mean-shift 7x7+8% -kuwahara 2 ... -remap palette` 후 같은 트레이싱은 312패스 / 18채우기 / 156 KB였지만 오브젝트가 덩어리로 합쳐졌다(cmp_zoom.png). 결론: 사후 정리로는 203X에 닿을 수 없다.
2. **헤드리스 Blender 플랫 아이소 시험 장면**(스크립트: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/vec-lane-scripts/flat_iso.py`; Workbench STUDIO, 플랫 면, 직교 54.736/0/45). `blender --factory-startup --python-expr`가 dither_intensity 기본값 = 1.0을 출력했다. 고유색: AA OFF + dither 0 → 43, AA OFF + 기본 dither → 222, AA 8 + dither 0 → 944, AA 8 + 기본 dither → 1,564.
3. **디더 영향.** `magick compare -metric AE` 결과 375,494 px(26%)가 최대 1/255 차이 났다. 주 회색 면의 정확한 색 마스크는 532,487 px에서 252,201 px로 줄었다. 디더된 마스크에 connected-components를 돌리면 'too many objects'로 실패했다(핀홀 65k개 초과, mask_zoom_dither.png 참조). vtracer 자체 클러스터링은 이를 대부분 흡수하므로(`-f 0 -p 8 -g 0`에서 56 대 55패스), 점 패턴은 색별 마스크 파이프라인과 팔레트 추출에 타격을 준다.
4. **디더 없는 플랫 렌더에서 VTracer 모드 비교**(구멍을 드러내려고 rsvg-convert로 #FF00FF 위에 렌더). stacked + polygon + palette(`-p 8 -g 0`): 44패스, 37채우기, 구멍 0 px, RMSE 1.35%. stacked + spline + `--simplify 1.0`: 44패스, 세그먼트 463 대 843, 구멍 0, RMSE 1.76%. cutout + polygon(팔레트 유무 무관, -f 0/1/2/4 모두 동일): 구멍 2,952 px에 공유 엣지의 분홍 헤어라인 이음매가 보임. 기본 spline(F1): 구멍 0이지만 상자 모서리가 둥글어짐(flat_cmp.png, zoom3.png).
5. **해상도 점검.** 원본 래스터는 1448x1086(pompeii), 1536x1024(colosseum), 1254x1254(pantheon, aqueduct)로 측정됐다. r23(사용자가 폐기한 이전 작업) 300 dpi PNG는 4961x7016이며, 콜로세움 900x700 크롭이 눈에 띄게 흐리다(crop_colosseum.png).
6. **메타데이터 점검.** 저장소 약 40개에 `gh api repos/...`(스타, pushed_at, 라이선스), 모델 라이선스·날짜에 Hugging Face API를 썼다(예: OmniSVG1.1_8B Apache-2.0 2026-03-30; FLUX.2-klein-9B flux-non-commercial; Qwen-Image-2.1 'other'; Krea-2 커뮤니티 라이선스). PyPI vtracer 최신 안정판은 0.6.15, 프리릴리스는 1.0.0a4. Comfy Cloud MCP의 search_models/search_templates로 카탈로그에 있는 ControlNet union과 벡터 파트너 템플릿을 확인했고, 아이소메트릭 LoRA가 없다는 것도 확인했다.
7. **메모.** 첫 크롭 직후(약 12:07-12:08) 사용자 지시로 이전 작업 폴더(`/Users/um-yunsang/roman-concrete-private-refs/artwork`, `.planning`)가 삭제됨(정상). 이 레인의 출력은 모두 `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/vec-lane/`에 있다.

## E-5. 후보 도구 표

### E-5-1. 후보 목록 (적합도 높은 순)

| 이름 | 단계 | 하는 일 | 적합도(1~5) | 라이선스 | 오픈소스 여부 | 유지보수 상태 | 주의사항 | URL |
|---|---|---|---|---|---|---|---|---|
| VTracer 1.0.0-alpha.4(visioncortex) | 벡터화 | 영역 클러스터링(색 또는 watershed), stacked 또는 이음매 없는 cutout 적층, polygon/spline/pixel 피팅, 고정 팔레트 스냅, --max-colors, --simplify, 출력 최적화를 갖춘 컬러 래스터→SVG 트레이서. | 5 | MIT | 예 | 스타 7,322; 2026-10-17 푸시; 최신 릴리스 1.0.0-alpha.4(2026-08-29); PyPI 안정판 0.6.15, 프리릴리스 1.0.0a4 | 알파 버전이다. 시험에서 cutout 모드가 얇은 영역을 빠뜨리고(-f 0에서도 구멍 2,952 px) 결합 이음매를 보였으므로, stacked를 쓰거나 밑에 받침 채우기를 깔 것. spline 모드 기본값은 상자 모서리를 둥글린다. polygon 모드는 30도 아이소 엣지를 1 px 단위로 계단화하는데, --simplify나 더 높은 렌더 해상도로 해결된다. | https://github.com/visioncortex/vtracer |
| Blender Workbench/EEVEE 플랫 렌더(헤드리스)를 트레이서 입력으로 | 플랫 렌더 | 플랫 셰이딩 면으로 직교 아이소메트릭 뷰를 렌더해 모든 평면이 정확히 한 색이 되게 한다. AA와 디더를 끄면 무손실로 트레이싱되는 정확한 팔레트 이미지가 나오고, Object Index / Cryptomatte 패스가 오브젝트별 마스크를 준다. | 5 | GPL-2.0-or-later | 예 | 활발(Blender 4.x/5.x); 로컬 바이너리가 헤드리스로 정상 실행됨 | 기본 dither 1.0 때문에 색이 43개에서 222개로 늘고, 정확한 색 마스크가 핀홀로 53% 손실됐다. STUDIO 조명의 톤은 스튜디오 라이트에 좌우되므로, 정확한 위/왼쪽/오른쪽 톤은 노멀로 구동하는 이미션 셰이딩으로 정할 것. 모델 제작 자체는 다른 레인이다. | https://www.blender.org/ |
| ImageMagick 7(-remap, -kmeans, -mean-shift, -kuwahara, -statistic Median, connected-components) | 전처리 / QA | 디더 없는 고정 팔레트 리매핑, k-means 팔레트 탐색, 엣지 보존 스무딩, 반점 제거, 구멍 검출(SVG를 마젠타 위에 렌더해 마젠타 픽셀 수를 셈). | 4 | ImageMagick License(Apache-2.0 계열) | 예 | 7.1.2-22 설치됨(빌드 2026-05-11) | 스무딩은 텍스처를 덩어리로 뭉갤 뿐이고, 회화풍 이미지를 플랫 지오메트리로 바꾸지 못한다(cmp_zoom.png에서 확인). | https://imagemagick.org/script/command-line-options.php |
| Qwen-Image-2512 + Fun ControlNet Union / InstantX Qwen-Image ControlNet Union | 생성(지오메트리 고정) | canny/depth/lineart/MLSD/pose 제어를 받는 text-to-image. Blender 자체의 깊이·엣지 패스로 지오메트리를 고정하고, 모델이 플랫 스타일 디테일(인물, 소품)을 더한다. | 4 | Apache-2.0(Qwen-Image-2512, InstantX union) | 예 | Qwen-Image-2512 2025-12-30 생성; InstantX union 2025-08-26 갱신; QwenLM/Qwen-Image 2026-02-10 푸시 | 20B 모델이라 로컬 디스크 9 GiB에는 너무 크므로 클라우드에서 실행한다. 출력은 여전히 래스터라 플랫화와 트레이싱이 필요하다. 프롬프트만으로 텍스처를 피할 수 있는지는 시험하지 않았으며, 플랫 스타일 LoRA나 편집 단계가 필요할 것으로 예상된다. | https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union |
| Qwen-Image-Edit-2511(Blender 렌더를 플랫 벡터 룩으로 재스타일) | 생성(이미지 편집 / 스타일) | 다중 이미지 참조를 지원하는 지시 기반 이미지 편집. 레이아웃을 유지한 채 플랫 셰이딩 Blender 렌더를 더 깔끔한 일러스트(창, 인부, 소품 추가)로 바꿀 수 있다. | 4 | Apache-2.0 | 예 | 2025-12-17 생성; lightx2v Lightning LoRA 있음 | 편집 모델은 지오메트리를 흐트러뜨릴 수 있으니 아이소 축을 다시 확인할 것. 203X 이미지를 참조로 넣지 말 것. | https://huggingface.co/Qwen/Qwen-Image-Edit-2511 |
| ComfyUI(+ Comfy Cloud 플러그인) | 생성 하네스 | 확산 모델, ControlNet, IP-Adapter, LoRA, 업스케일러를 위한 노드 그래프 런타임. | 4 | GPL-3.0 | 예 | 스타 138k; 2026-10-18 푸시 | 클라우드 실행은 크레딧을 소모한다. 클라우드 카탈로그에 아이소메트릭 LoRA가 없어서 가져와야 한다. | https://github.com/comfyanonymous/ComfyUI |
| SVGO | 후처리 | SVG 최적화: 패스 데이터 정밀도, 병합, 정리. | 4 | MIT | 예 | 스타 22.7k; 2026-08-27 푸시 | 오브젝트별 레이어 편집성을 유지하려면 mergePaths와 collapseGroups를 끌 것. | https://github.com/svg/svgo |
| OpenCV(pyrMeanShiftFiltering, bilateralFilter, edgePreservingFilter, morphology) | 전처리 | 엣지 보존 스무딩과 색별 마스크의 형태학적 open/close로 트레이싱 전에 고립 픽셀을 없앤다. | 3 | Apache-2.0 | 예 | 스타 91k; 2026-10-16 푸시 | 모든 스무딩과 같은 한계: 깨끗한 지오메트리를 만들어 내지 못한다. | https://github.com/opencv/opencv |
| Potrace 1.16(및 Python 포트 potracer) | 벡터화(마스크별) | 고품질 1비트 비트맵→베지어 트레이서. 주요 옵션: -t turdsize(반점, 기본 2), -a alphamax(코너, 기본 1; 0이면 폴리곤), -O opttolerance(0.2), -z turnpolicy. | 3 | GPL-2.0-or-later(Icosasoft 상용 라이선스 있음) | 예 | 1.16, 2019-09-17 릴리스(안정적이나 비활성); tatarize/potrace 포트 GPL-2.0, 마지막 푸시 2024-05 | 흑백 전용이다. 컬러 작업에는 색마다 마스크가 필요하고, 그 마스크가 디더 없는 입력에서 나와야 핀홀로 차지 않는다. GPL이다. | https://potrace.sourceforge.net/ |
| Z-Image-Turbo + alibaba-pai Fun ControlNet Union 2.1 + ISOMETRIC-REDMOND-ZIMAGE LoRA | 생성(지오메트리 고정, 고속) | Canny/HED/Depth/Pose/MLSD union 제어를 갖춘 6B 증류 text-to-image. Apache-2.0 아이소메트릭 스타일 LoRA가 있다(트리거 ISOMETRIC / ISOMETRICREDM). | 3 | Apache-2.0(베이스, ControlNet, LoRA) | 예 | Z-Image-Turbo 2026-01-30 갱신; LoRA 2026-07-20 갱신 | LoRA의 학습 데이터가 공개되지 않았고, 룩(3D 렌더 아이소메트릭인지 플랫 벡터인지)도 확인하지 않았다. 로컬 가중치는 9 GiB 여유 디스크에 부담이 된다. | https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1 |
| Qwen-Image-Layered | 생성 / 레이어 분해 | 이미지를 3-8개 이상의 RGBA 레이어로(재귀적으로) 나눠 각각 따로 편집할 수 있게 한다. | 3 | Apache-2.0 | 예 | 2025-12-19; 저장소 2025-12-31 푸시 | 파라미터 20B, 권장 해상도 640(A2 디테일에는 너무 낮음). ComfyUI 지원이 명시되지 않았다. 여기서 시험하지 않았다. | https://huggingface.co/Qwen/Qwen-Image-Layered |
| mflux(Apple Silicon용 MLX 네이티브 이미지 모델) | 생성 런타임(로컬) | Z-Image, Qwen-Image, FLUX.2/3 Klein, Krea 2 등을 M 시리즈 GPU에서 네이티브로 돌리며, ControlNet Union(Z-Image, Qwen-Image-2.1), depth, Redux, LoRA, SeedVR2 업스케일링을 지원한다. | 3 | MIT | 예 | 스타 2.5k; 2026-10-17 푸시 | 모델 가중치가 각각 수 GB라 9 GiB 여유로는 빠듯하다. q4 양자화 변형이 있다. | https://github.com/filipstrand/mflux |
| Real-ESRGAN(anime 6B 모델) | 전처리(업스케일) | 엣지를 선명하게 유지하는 업스케일링. anime 모델은 플랫 컬러 아트에 맞는다. | 3 | BSD-3-Clause | 예 | 스타 37k; 마지막 푸시 2024-08(오래됐지만 안정적) | 디테일을 복원하지는 못한다. 텍스처 있는 입력에 쓰면 주기적 아티팩트를 더할 수 있다. Upscayl(AGPL-3.0)은 GUI 래퍼다. | https://github.com/xinntao/Real-ESRGAN |
| paper.js(simplify, 불리언 연산), Bun 스크립트로 사용 | 후처리 | 패스 단순화, 불리언 union/subtract, 지오메트리 스냅. | 3 | MIT | 예 | 스타 15k; 마지막 푸시 2024-07 | 스냅 스크립트는 직접 작성해야 하며, 기성 기능이 아니다. | https://github.com/paperjs/paper.js |
| Vectorizer.AI(독점, 비교용) | 벡터화(상용) | 도형 전체(원, 타원, 둥근 사각형, 별)를 피팅하고 풀컬러·안티앨리어스를 처리하는 딥러닝 트레이서. SVG/EPS/PDF/DXF 출력, 입력 한도 3 MP. | 3 | 독점(약관상 출력물을 ML 학습에 쓰는 것 금지) | 아니요 | 운영 중인 서비스 | 유료다. 3 MP 입력 상한은 A2에 비해 작다. | https://vectorizer.ai/ |
| ComfyUI-ToSVG | 벡터화(그래프 내) | ComfyUI 노드: ConvertRasterToVector(vtracer), Potrace B/W, Image Quantize, 패스 단순화, SaveSVG. | 2 | MIT | 예 | 스타 316; 2025-06-20 푸시 | requirements.txt가 그냥 'vtracer'라고 적어서 PyPI 0.6.15가 설치된다. 고정 팔레트, 이음매 없는 cutout, --simplify가 없다. 로컬 1.0 CLI가 더 나은 선택이다. | https://github.com/Yanick112/ComfyUI-ToSVG |
| comfyui_controlnet_aux | 생성(제어 전처리기) | ControlNet용 lineart, depth, normal, canny, MLSD 전처리기. | 2 | Apache-2.0 | 예 | 스타 4.2k; 2026-10-11 푸시 | 회화풍 이미지에서 추정한 깊이나 선은 같은 모호함을 그대로 끌고 온다. | https://github.com/Fannovel16/comfyui_controlnet_aux |
| SDXL + xinsir controlnet-union-sdxl-1.0 + IP-Adapter(ComfyUI_IPAdapter_plus) | 생성(스타일 참조) | 성숙한 SDXL 제어 스택. IP-Adapter가 스타일 참조 이미지를 공급한다. | 2 | SDXL OpenRAIL++; xinsir union Apache-2.0; h94 IP-Adapter Apache-2.0; ComfyUI_IPAdapter_plus GPL-3.0 | 예 | IPAdapter_plus 마지막 푸시 2025-04-14(유지보수 모드) | 구세대 모델이다. 203X 이미지를 IP-Adapter 참조로 쓰지 말 것. | https://huggingface.co/xinsir/controlnet-union-sdxl-1.0 |
| FLUX.1-dev / Redux / Depth / Kontext + Shakker ControlNet Union Pro 2.0 + Flux 아이소메트릭 LoRA | 생성 | 깊이 제어, Redux 이미지 변형 스타일 참조, 다수의 커뮤니티 아이소메트릭 LoRA(예: strangerzonehf/Flux-Isometric-3D-LoRA)를 갖춘 고품질 확산 모델. | 2 | FLUX.1-dev 비상업 라이선스(Redux, Depth, Kontext-dev도 마찬가지); Shakker union 'other'; LoRA는 제각각 | 아니요 | FLUX.1-dev 2025-06-27 갱신 | 가중치는 공개돼 있지만 OSI 기준 오픈이 아니다. dev 라이선스는 모델 자체의 사용을 제한하며, 출력물에 대한 조건은 확인해야 한다. 대부분의 아이소메트릭 LoRA는 플랫 벡터가 아니라 광택 있는 3D 룩을 낸다. | https://huggingface.co/black-forest-labs/FLUX.1-dev |
| FLUX.2-klein-4B | 생성 | 작은 Apache-2.0 FLUX.2 text-to-image·편집 모델. | 2 | Apache-2.0(9B 변형은 비상업) | 예 | 2026-02-24 갱신 | 시험하지 않았다. | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B |
| SAM 2 / SAM 3(Segment Anything) | 전처리(오브젝트 마스크) | Blender 오브젝트 ID가 없는 AI 이미지에 오브젝트별 마스크를 주는 프롬프트 기반 분할. | 2 | SAM 2 Apache-2.0; SAM 3 'NOASSERTION'(커스텀 라이선스) | 예 | sam2 2026-05-30 푸시; sam3 2026-10-14 푸시 | SAM 3 라이선스를 확인할 것. Blender에서 나온 지오메트리에는 필요 없다. | https://github.com/facebookresearch/sam2 |
| pngquant / libimagequant | 전처리(팔레트 탐색) | 고품질 적응형 팔레트 양자화. | 2 | GPL-3.0-or-later(상용 라이선스 있음) | 예 | pngquant 스타 5.8k, 2026-06-21 푸시 | 디더링을 피하려면 --nofs를 쓸 것. 디더는 핀홀 문제를 다시 만든다. | https://pngquant.org/ |
| OmniSVG / OmniSVG 1.1(4B, 8B) | AI text/image-to-SVG | SVG 토큰을 직접 쓰는 Qwen2.5-VL 기반 모델. 아이콘부터 애니메 캐릭터까지 text-to-SVG와 image-to-SVG를 한다. | 2 | Apache-2.0(MMSVG 데이터셋은 CC BY-NC-SA 4.0) | 예 | 스타 2.6k; 2026-03-01 푸시; 1.1 가중치 2026-03-30; NeurIPS 2025 | CUDA에서 약 26 GB VRAM 필요(8B). 4,096 토큰에 98초. MPS 경로가 문서화되지 않았다. 복잡도가 A2 아이소 장면에 한참 못 미친다. | https://github.com/OmniSVG/OmniSVG |
| Recraft V4 / V4.1 Vector, Quiver Arrow 2(독점, 비교용, Comfy Cloud 파트너 템플릿 경유) | AI text/image-to-SVG(상용) | 네이티브 SVG 생성(Recraft V4 2026년 2월, V4.1 vector 2026년 5월)과 image-to-SVG(Quiver Arrow 2). | 2 | 독점 API | 아니요 | 운영 중(Comfy Cloud 템플릿 api_recraft_v4_1_text_to_vector, api_quiver_arrow2_image_to_svg) | 품질 주장은 벤더 자신의 주장이다. 크레딧을 소모한다. | https://www.recraft.ai/docs/recraft-models/recraft-V4 |
| ImageTracerJS | 벡터화 | 간단한 JS 컬러 트레이서(ltres/qtres, pathomit, 고정 팔레트 옵션, 색 양자화 사이클, blur). | 1 | Unlicense | 예 | 스타 1.5k; 마지막 푸시 2023-11 | 유지보수되지 않는다. | https://github.com/jankovicsandras/imagetracerjs |
| AutoTrace | 벡터화(중심선) | 외곽선·중심선 트레이싱. 단일 획 선화에 유용하다. | 1 | GPL-2.0 | 예 | 스타 744; 2026-10-13 푸시; 마지막 태그 릴리스 0.31.10(2024-01) | 컬러 모드는 VTracer보다 약하다. | https://github.com/autotrace/autotrace |
| Inkscape Trace Bitmap | 벡터화(GUI) | Potrace 기반 단일 스캔·다중 스캔 컬러 트레이싱, autotrace, 중심선, 픽셀아트 모드. | 1 | GPL-2.0-or-later | 예 | GitLab 릴리스 API가 반환한 최신 태그는 INKSCAPE_1_4(2024-10-12) | 이 레인을 위해 설치할 가치가 없다. | https://gitlab.com/inkscape/inkscape |
| StarVector(1B, 8B im2svg) + RLRF | AI image-to-SVG | 이미지에서 SVG 코드를 쓰는 비전-언어 모델. RLRF(NeurIPS 2025)는 렌더링 피드백 기반 강화학습을 더한다. | 1 | Apache-2.0 | 예 | 스타 4.6k; 2025-11-07 푸시; 가중치 2025-03-19 | 컨텍스트 8k-16k 토큰. | https://github.com/joanrod/star-vector |
| LayerTracer(ICCV 2025) | AI 레이어 SVG 생성 | FLUX 확산 트랜스포머가 단계별 구성 이미지를 생성하고, 이를 레이어별로 벡터화하면서 패스 중복을 제거한다. | 1 | MIT(코드); FLUX.1 베이스 라이선스 적용 | 예 | 스타 98; 2025-04-01 푸시 | 가중치는 Google Drive 링크로 배포된다. 일러스트에 맞지 않는다. | https://github.com/showlab/LayerTracer |
| LLM4SVG(CVPR 2025) | AI text-to-SVG | SVGX 데이터셋(250k / 1M)으로 LLM/VLM을 미세조정해 SVG를 이해·생성한다. | 1 | MIT(코드); 데이터셋 라이선스 미명시 | 예 | 스타 672; 2025-05-22 푸시 | 쓸 수 있는 체크포인트가 없다. | https://github.com/ximinng/LLM4SVG |
| Chat2SVG(CVPR 2025) | AI text-to-SVG | LLM이 SVG 템플릿을 쓰고, SDXL+ControlNet과 SAM이 디테일을 더하고, 잠재 SVG VAE와 diffvg가 도형을 최적화한다. | 1 | 없음(모든 권리 보유로 간주) | 아니요 | 스타 254; 2025-04-02 푸시 | 라이선스가 없으면 법적으로 재사용할 수 없다. | https://github.com/kingnobro/Chat2SVG |
| PyTorch-SVGRender(LIVE, DiffVG, CLIPasso, VectorFusion, DiffSketcher, SVGDreamer) | AI 최적화 기반 SVG | 이미지 벡터화와 score distillation을 통한 text-to-SVG를 위한 미분 가능 래스터라이저 방법 모음. | 1 | MPL-2.0(SVGDreamer MIT, LIVE Apache-2.0, VectorFusion-pytorch MIT) | 예 | 스타 496; 2025-02-25 푸시; SVGDreamer 2025-05-01 푸시; LIVE 마지막 푸시 2024-02 | 연구용 코드다. 인쇄 품질이 아니다. | https://github.com/ximinng/PyTorch-SVGRender |
| DiffVG / pydiffvg | 미분 가능 래스터라이저(연구) | LIVE, VectorFusion 등의 바탕이 되는 미분 가능 벡터 래스터화. | 1 | Apache-2.0 | 예 | 스타 1.3k; 2025-05-17 푸시 | CUDA 중심이다. | https://github.com/BachiLi/diffvg |
| NeuralSVG | AI text-to-SVG | score distillation으로 최적화한 암시적 신경 표현으로, 순서 있고 레이어화된 미니멀 SVG를 만든다. | 1 | MIT | 예 | 스타 1.4k; 2025-12-15 푸시 | 재현할 수 없다(diffvg 무작위성). | https://github.com/SagiPolaczek/NeuralSVG |
| LayerPeeler(SIGGRAPH Asia 2025) / SuperSVG(CVPR 2024) | AI 레이어 이미지 벡터화 | LayerPeeler는 이미지를 자기회귀적으로 한 겹씩 벗겨 편집 가능한 레이어로 만들고, SuperSVG는 슈퍼픽셀 기반 벡터화를 쓴다. | 1 | 없음 | 아니요 | LayerPeeler 스타 37, 2025-12-29 푸시; SuperSVG 스타 76, 2026-04-12 푸시 | 라이선스가 없으므로 재사용할 권리가 없다. | https://github.com/kingnobro/LayerPeeler |
| VectorArk(CVPR 2026) / VFig / DuetSVG(2025-2026 연구) | AI image-to-SVG(연구 SOTA) | VectorArk: 둥근 폴리곤 프리미티브와 실사 이미지용 열화 모델을 쓰는 VLM 벡터화(Adobe 저자). VFig: 도표/다이어그램→SVG. DuetSVG: 이미지와 SVG 토큰을 함께 생성. | 1 | 미상 / 미공개(미확인) | 아니요 | arXiv 2026년 5월 / 2026년 3월 / 2025년 12월 | 공개 여부를 확인하지 않았다. https://vectorark.github.io/ 를 확인할 것. | https://arxiv.org/abs/2605.24398 |

### E-5-2. 후보별 보충 정보 (적합 이유 · 로컬 설치 · 에이전트 구동 · 근거 URL)

1. **VTracer 1.0.0-alpha.4**
   - 적합 이유: 플랫 입력에 가장 좋은 OSS 컬러 트레이서다. 1.0의 팔레트·simplify 기능이 203X식 고정 팔레트에 그대로 들어맞는다. 시험에서 플랫 Blender 렌더에 대해 44패스, 구멍 0, RMSE 1.35%를 냈다. 권장 플랫 아트 설정: `--hierarchical stacked --mode polygon -p 8 -g 0 -f 8-32 --palette-file P`(건축), `--mode spline --simplify 0.75-1.5 --corner-threshold 60`(인물).
   - 로컬 설치: 예: `/Users/um-yunsang/roman-concrete-private-refs/.tools/vtracer/vtracer`(1.0.0-alpha.4)
   - 에이전트 구동: CLI, Rust/Python/JS 라이브러리
   - 근거: https://github.com/visioncortex/vtracer, https://github.com/visioncortex/vtracer/releases/tag/1.0.0-alpha.4, https://pypi.org/project/vtracer/
2. **Blender Workbench/EEVEE 플랫 렌더(헤드리스)**
   - 적합 이유: 203X처럼 선명하고 일관된 아이소 지오메트리를 면당 적은 톤으로 주는, 이 레인이 찾은 유일한 경로다. 필수 설정: `scene.display.render_aa='OFF'`, `scene.render.dither_intensity=0`(기본값 1.0), `view_transform='Standard'`, 플랫 면, 직교 카메라(54.736, 0, 45도).
   - 로컬 설치: 예: `/opt/homebrew/bin/blender`, 그리고 메인 세션의 Blender MCP
   - 에이전트 구동: CLI(`blender -b -P script.py`), bpy 스크립팅, MCP
   - 근거: https://www.blender.org/
3. **ImageMagick 7**
   - 적합 이유: 설치돼 있고 스크립트로 쓸 수 있다. 프로젝트 팔레트로 `-dither None` 리매핑하는 것이 AI 래스터를 트레이싱하기 전의 핵심 단계이고, 마젠타 배경 점검이 밝은 점·구멍 결함을 자동으로 잡아낸다.
   - 로컬 설치: 예: `/opt/homebrew/bin/magick`
   - 에이전트 구동: CLI
   - 근거: https://imagemagick.org/script/command-line-options.php
4. **Qwen-Image-2512 + Fun ControlNet Union / InstantX Qwen-Image ControlNet Union**
   - 적합 이유: 베이스와 ControlNet이 모두 Apache-2.0이고 둘 다 이미 Comfy Cloud 카탈로그에 있다. 프롬프트 충실도가 강하고, 상업 포스터에 문제가 없다.
   - 로컬 설치: 아니요(Comfy Cloud에서 사용 가능)
   - 에이전트 구동: Comfy Cloud MCP(submit_workflow, 템플릿 image_qwen_Image_2512_controlnet)
   - 근거: https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union, https://github.com/QwenLM/Qwen-Image
5. **Qwen-Image-Edit-2511**
   - 적합 이유: Apache-2.0이고 Lightning LoRA 덕분에 빠르다. 직접 만든 플랫 렌더를 스타일 참조로 쓰면 203X 저작권 노출을 피할 수 있다.
   - 로컬 설치: 아니요
   - 에이전트 구동: Comfy Cloud 워크플로
   - 근거: https://huggingface.co/Qwen/Qwen-Image-Edit-2511
6. **ComfyUI(+ Comfy Cloud 플러그인)**
   - 적합 이유: 사용자에게 이미 Comfy Cloud MCP가 있다. 워크플로를 저장해 오브젝트별로 다시 돌릴 수 있어, 지오메트리를 고정한 플랫 렌더를 묶음으로 처리하기에 맞다.
   - 로컬 설치: 클라우드 전용(플러그인 연결됨)
   - 에이전트 구동: MCP(comfy-cloud) / JSON API
   - 근거: https://github.com/comfyanonymous/ComfyUI, https://comfy.org/
7. **SVGO**
   - 적합 이유: Figma로 가져오기 전에 트레이싱된 SVG를 줄인다. bunx로 실행할 수 있다.
   - 로컬 설치: 아니요(`bunx svgo`)
   - 에이전트 구동: CLI
   - 근거: https://github.com/svg/svgo
8. **OpenCV**
   - 적합 이유: 이미 import할 수 있다(시스템 python3에 cv2 5.0.0). AI가 생성한 플랫 이미지를 오브젝트별로 스크립트 정리하기에 좋다.
   - 로컬 설치: 예(`python3 -c 'import cv2'`가 5.0.0을 보고)
   - 에이전트 구동: Python 스크립팅
   - 근거: https://github.com/opencv/opencv
9. **Potrace 1.16(및 potracer)**
   - 적합 이유: Blender Object-Index나 Cryptomatte 마스크에서 오브젝트별 또는 팔레트 색별로 따로 트레이싱하면 매우 매끄러운 외곽선을 얻는다. Inkscape의 다중 스캔 트레이스가 이 방식이다. 제안 설정: `-t 8 -a 0.8 -O 0.4`.
   - 로컬 설치: 아니요(ComfyUI-ToSVG가 potracer를 끌어옴)
   - 에이전트 구동: CLI / Python(potracer)
   - 근거: https://potrace.sourceforge.net/, https://github.com/tatarize/potrace
10. **Z-Image-Turbo + Fun ControlNet Union 2.1 + ISOMETRIC-REDMOND-ZIMAGE LoRA**
    - 적합 이유: 전부 Apache-2.0이다. Comfy Cloud 템플릿이 있다(image_z_image_turbo_fun_union_controlnet). mflux가 ControlNet Union과 함께 Apple Silicon에서 네이티브로 돌린다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Comfy Cloud MCP, 로컬은 mflux CLI
    - 근거: https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1, https://huggingface.co/artificialguybr/ISOMETRIC-REDMOND-ZIMAGE
11. **Qwen-Image-Layered**
    - 적합 이유: AI로 디테일을 더한 오브젝트를 트레이싱 전에 하위 레이어로 나눌 수 있어, Figma에서 SVG 편집성을 유지하는 데 도움이 된다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python / diffusers(CUDA, bf16)
    - 근거: https://huggingface.co/Qwen/Qwen-Image-Layered, https://github.com/QwenLM/Qwen-Image-Layered
12. **mflux**
    - 적합 이유: Mac에서 실용적인 유일한 로컬 OSS 실행기이며, CLI를 에이전트가 구동할 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: CLI
    - 근거: https://github.com/filipstrand/mflux
13. **Real-ESRGAN(anime 6B 모델)**
    - 적합 이유: 작은 오브젝트를 트레이싱 전에 2배 업스케일하면 계단과 반점이 줄어든다.
    - 로컬 설치: 아니요
    - 에이전트 구동: CLI / ncnn-vulkan 바이너리
    - 근거: https://github.com/xinntao/Real-ESRGAN
14. **paper.js**
    - 적합 이유: 트레이싱된 엣지를 아이소 각도(30/90/150도)에 스냅하고, 같은 색 이웃을 병합하고, N px² 미만 슬리버를 지우는 작은 Bun 스크립트에 쓴다.
    - 로컬 설치: 아니요
    - 에이전트 구동: JS 스크립팅(Bun)
    - 근거: https://github.com/paperjs/paper.js
15. **Vectorizer.AI(독점, 비교용)**
    - 적합 이유: 플랫 아이콘·소품을 깨끗하게 트레이싱하는 기준점이다. 그래도 플랫 입력이 필요하다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 웹 / API
    - 근거: https://vectorizer.ai/
16. **ComfyUI-ToSVG**
    - 적합 이유: ComfyUI 그래프 안에서 트레이싱까지 처리하기에 편리하다.
    - 로컬 설치: 아니요
    - 에이전트 구동: ComfyUI 노드
    - 근거: https://github.com/Yanick112/ComfyUI-ToSVG, https://pypi.org/project/vtracer/
17. **comfyui_controlnet_aux**
    - 적합 이유: Blender 자체 패스가 없을 때만 유용하다. Blender의 정확한 Z/노멀/Freestyle 패스가 회화풍 래스터에서 추정한 것보다 나은 제어 이미지다.
    - 로컬 설치: 아니요
    - 에이전트 구동: ComfyUI 노드
    - 근거: https://github.com/Fannovel16/comfyui_controlnet_aux
18. **SDXL + xinsir controlnet-union-sdxl-1.0 + IP-Adapter**
    - 적합 이유: 라이선스가 관대하고 SDXL union 모델이 Comfy Cloud에 있지만, 프롬프트 충실도와 디테일이 Qwen/Z-Image보다 낮다. IP-Adapter는 직접 만든 참조 이미지로만 쓸 수 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Comfy Cloud
    - 근거: https://huggingface.co/xinsir/controlnet-union-sdxl-1.0, https://github.com/cubiq/ComfyUI_IPAdapter_plus, https://huggingface.co/h94/IP-Adapter
19. **FLUX.1-dev / Redux / Depth / Kontext + Shakker ControlNet Union Pro 2.0 + Flux 아이소메트릭 LoRA**
    - 적합 이유: 기술적으로는 유능하지만 가중치가 비상업 라이선스라, 공개되거나 클라이언트용으로 인쇄될 수 있는 포스터의 기본 선택으로는 맞지 않는다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Comfy Cloud / diffusers
    - 근거: https://huggingface.co/black-forest-labs/FLUX.1-dev, https://huggingface.co/Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro-2.0, https://huggingface.co/strangerzonehf/Flux-Isometric-3D-LoRA
20. **FLUX.2-klein-4B**
    - 적합 이유: 라이선스가 관대하고 작아서 mflux로 로컬 실행할 수 있을지 모른다. ControlNet 지원은 확인하지 않았다.
    - 로컬 설치: 아니요
    - 에이전트 구동: mflux / ComfyUI
    - 근거: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
21. **SAM 2 / SAM 3**
    - 적합 이유: 사람이나 소품 하나하나를 Figma용 별도 SVG 레이어로 트레이싱·그룹화할 수 있게 해 준다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python
    - 근거: https://github.com/facebookresearch/sam2, https://github.com/facebookresearch/sam3
22. **pngquant / libimagequant**
    - 적합 이유: 팔레트를 자동으로 찾는 데는 도움이 되지만 고정된 프로젝트 팔레트를 강제할 수는 없다. 그 일은 ImageMagick -remap이나 vtracer --palette-file이 한다.
    - 로컬 설치: 아니요
    - 에이전트 구동: CLI
    - 근거: https://pngquant.org/, https://github.com/kornelski/pngquant
23. **OmniSVG / OmniSVG 1.1**
    - 적합 이유: 가장 좋은 오픈 가중치 SVG 모델이지만, 정보 패널의 작은 픽토그램·아이콘(음식, 도구, 타임라인 아이콘)에만 쓸 수 있고 랜드마크에는 쓸 수 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python inference.py(CUDA)
    - 근거: https://github.com/OmniSVG/OmniSVG, https://huggingface.co/OmniSVG/OmniSVG1.1_8B, https://arxiv.org/abs/2504.06263
24. **Recraft V4 / V4.1 Vector, Quiver Arrow 2**
    - 적합 이유: 정보 패널 픽토그램을 비교해 보는 데 유용하다. 로고, 아이콘, 단순 일러스트용으로 포지셔닝돼 있고, 조밀한 아이소 장면용이 아니다.
    - 로컬 설치: 클라우드 API
    - 에이전트 구동: Comfy Cloud MCP 파트너 템플릿
    - 근거: https://www.recraft.ai/docs/recraft-models/recraft-V4, https://quiver.ai/
25. **ImageTracerJS**
    - 적합 이유: 설치 없이 Bun에서 돌아가지만 품질과 속도가 VTracer 1.0에 크게 못 미친다.
    - 로컬 설치: 아니요
    - 에이전트 구동: JS
    - 근거: https://github.com/jankovicsandras/imagetracerjs
26. **AutoTrace**
    - 적합 이유: 중심선 모드로 지시선이나 손그림 획을 벡터화할 수 있지만, 그런 것은 Figma에서 직접 그리는 편이 쉽다.
    - 로컬 설치: 아니요
    - 에이전트 구동: CLI
    - 근거: https://github.com/autotrace/autotrace
27. **Inkscape Trace Bitmap**
    - 적합 이유: VTracer 1.0 + potrace에 더하는 것이 없고, 설치돼 있지도 않다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 대부분 GUI(트레이스용 CLI 액션은 제한적)
    - 근거: https://gitlab.com/inkscape/inkscape, https://inkscape-manuals.readthedocs.io/en/latest/tracing-an-image.html
28. **StarVector(1B, 8B im2svg) + RLRF**
    - 적합 이유: README에 'will not work for natural images or illustrations'라고 명시돼 있다. 아이콘, 로고, 다이어그램에서만 강하다(SVG-Bench Icons DinoScore 0.984 vs VTracer 0.940).
    - 로컬 설치: 아니요
    - 에이전트 구동: Python / vLLM(CUDA)
    - 근거: https://github.com/joanrod/star-vector, https://huggingface.co/starvector/starvector-8b-im2svg, https://arxiv.org/abs/2505.20793
29. **LayerTracer**
    - 적합 이유: 공개된 가중치는 9칸 격자 검은 선 아이콘과 이모지만 다루며, 약 50 GB의 메모리가 필요하다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 셸 스크립트(CUDA)
    - 근거: https://github.com/showlab/LayerTracer, https://arxiv.org/html/2502.01105v3
30. **LLM4SVG**
    - 적합 이유: 가중치 링크가 여전히 'pending'으로 표시돼 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python
    - 근거: https://github.com/ximinng/LLM4SVG
31. **Chat2SVG**
    - 적합 이유: 단순한 오브젝트 규모다. CUDA와 diffvg가 필요하고, 라이선스 파일이 없다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python + Claude/OpenAI API
    - 근거: https://github.com/kingnobro/Chat2SVG
32. **PyTorch-SVGRender**
    - 적합 이유: 이미지마다 정해진 개수의 패스를 최적화하고, 수 분에서 수 시간이 걸리며, 뭉툭하고 순서 없는 도형을 낸다. Apple MPS를 지원하지 않는 DiffVG에 의존한다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python(CUDA)
    - 근거: https://github.com/ximinng/PyTorch-SVGRender, https://github.com/ximinng/SVGDreamer, https://github.com/Picsart-AI-Research/LIVE-Layerwise-Image-Vectorization, https://github.com/ximinng/VectorFusion-pytorch
33. **DiffVG / pydiffvg**
    - 적합 이유: Apple Silicon에서 빌드하기가 어렵다. 이슈 #72 'Mac / MPS Support'가 열려 있다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python
    - 근거: https://github.com/BachiLi/diffvg, https://github.com/BachiLi/diffvg/issues/72
34. **NeuralSVG**
    - 적합 이유: 미니멀한 아이콘 같은 출력이다. diffvg가 필요하고, README가 오브젝트가 적은 단순한 프롬프트를 요구한다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python
    - 근거: https://github.com/SagiPolaczek/NeuralSVG
35. **LayerPeeler / SuperSVG**
    - 적합 이유: 편집성 면에서 흥미롭지만 두 저장소 모두 라이선스가 없고, 더 단순한 그래픽을 대상으로 한다.
    - 로컬 설치: 아니요
    - 에이전트 구동: Python(CUDA)
    - 근거: https://github.com/kingnobro/LayerPeeler, https://github.com/sjtuplayer/SuperSVG
36. **VectorArk / VFig / DuetSVG**
    - 적합 이유: 분야가 가는 방향을 보여 주지만, 이 용도로 쓸 공개 가중치가 확인되지 않았고 대상이 도표와 아이콘이다.
    - 로컬 설치: 아니요
    - 에이전트 구동: 해당 없음(n/a)
    - 근거: https://arxiv.org/abs/2605.24398, https://arxiv.org/html/2603.24575v1, https://arxiv.org/abs/2512.10894, https://arxiv.org/abs/2602.21416
