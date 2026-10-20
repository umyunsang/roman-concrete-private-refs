# 2차-3 Blender 정밀 모델링 조사 보고서

- 조사 범위: Blender(오픈소스) 경로. 참조 이미지 수준의 정밀한 3D 미니어처 디오라마를, 가능한 곳은 에이전트로 구동해 만드는 방법을 조사했다. 기준 환경은 M1/16 GB에서 돌리는 Blender 5.2.2 LTS다.
- 배경(작업 지시 기준): 로마 콘크리트를 주제로 한 A2 세로 인포그래픽 포스터. 정보 디자인 벤치마크는 한국 스튜디오 203X의 포스터이고, 2.5D/3D 모델 수준의 기준은 사용자가 준 이소메트릭 미니어처 콜로세움 디오라마 이미지다. 작업 지시에 따르면 그 이미지는 Nano Banana Pro로 만든 AI 이미지로 확인됐다. 이 레인의 원문은 출처를 '가능성 매우 높음, 증명 불가'로 적었고, 아래에는 원문 판단을 그대로 옮겼다. 사용자 장비는 Apple M1·16GB RAM·디스크 여유 약 17GB이며, 사용자는 한국에 있다.
- 원문 입력: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/wf2/3-real-3d-blender.json`

---

## 1. 한눈에 보는 결론

- 참조 이미지는 Google Gemini 3 계열(Nano Banana) 이미지 모델의 출력일 가능성이 매우 높다(증명은 불가). 그 뒤에 3D 모델은 없다. 따라서 구해야 할 자산이 아니라 맞춰야 할 '룩(LOOK)' 목표로 다룬다.
- Blender 5.2.2 + Geometry Nodes + Cycles(Metal) 경로만으로 참조의 구도·조명·구조적 깊이·석재별 변화를 맞출 수 있다. 정확도와 6개 랜드마크 간 일관성은 참조보다 낫다. 핵심 도구는 모두 **M1 로컬 실행 가능**하고 **상업·인쇄 사용 가능**하다.
- 격차는 기하나 렌더링이 아니라 세트 드레싱(소품·인물·식생·풍화)에 있다. 에이전트 단독으로는 참조 풍부함의 약 70%에 그칠 가능성이 크다. 사람의 아트 디렉션 2~3일을 더하면 약 80~90%에 이른다.
- 총 작업량은 약 6~9 에이전트-일과 사람 2~3일이다. 렌더링은 M1 로컬에서 약 하룻밤 걸린다.
- Tencent Hunyuan3D 라이선스는 **한국을 적용 지역에서 제외**하므로 포스터에 쓰지 않는다. **NC/ND(비상업·변경금지) 에셋도 금지**한다. CC-BY 에셋은 포스터에 크레딧 블록이 필요하다.

---

## 2. 핵심 발견

1. **참조 이미지의 출처(가능성 매우 높음, 증명 불가)**
   - 1376x768은 Google Gemini 3 계열 이미지 모델이 문서에 적어 둔 16:9 '1K' 출력 크기와 정확히 같다. Nano Banana 2.1, Gemini 3.1 Flash Image, 3.1 Pro Image 모두 16:9 = 1376x768로 명시한다. Gemini 2.5 Flash Image는 1344x768을 낸다(출처: ai.google.dev/gemini-api/docs/image-generation, 최종 업데이트 2026-10-09).
   - 파일에는 APP/EXIF/XMP/C2PA 세그먼트가 전혀 없다. Supabase/Cloudflare CDN이 이를 제거하기 때문이다. 따라서 파일 자체로는 AI 여부를 증명할 수도, 배제할 수도 없다.
   - Last-Modified와 파일명 타임스탬프 모두 업로드 날짜를 2026-02-10으로 가리킨다.
   - AI의 시각적 징후는 다음과 같다.
     - 바깥 아케이드 층들이 수직으로 맞지 않는다. 실제 콜로세움은 80개 베이가 모두 수직으로 쌓인다.
     - 방사형 cavea 벽과 hypogeum 배치는 지어낸 것이다.
     - 사람은 뭉개진 덩어리다.
     - 부서진 꼭대기는 평평한 판이다.
   - localbanana.io 사이트는 모델 이름을 밝히지 않는다.
   - 사용자 측에서는 Gemini 앱의 Google SynthID 검증으로 확인할 수 있다.
   - 결론: 그 뒤에 3D 모델은 없다. 구할 자산이 아니라 룩 목표로 다룬다.

2. **이 장비에서 직접 잰 보정 수치(가벼운 테스트)**
   - 조건: Blender 5.2.2, 7코어 M1 GPU의 Cycles Metal, OIDN, adaptive sampling.
   - 테스트 장면: 타원형 3층·80베이 아케이드 프록시, 단색 재질, 태양+월드 조명, 직교 카메라.
   - 960x540/64spp: 8.6 s.
   - 1920x1080/128spp: 인스턴스 약 63k개일 때 37.9 s, 인스턴스 자갈 약 1.18M개일 때 53.1 s.
   - 같은 두 장면을 EEVEE 1080p로 렌더하면 3.3 s와 15.0 s.
   - 최대 RAM은 3.5-4.7 GB였다. 인스턴싱은 부담이 적다.
   - 참조 수준 장면(텍스처, 알파 식생, 3-4 바운스, 인스턴스 삼각형 약 5-15M, 약 3-6배 느림)으로 외삽한 값은 다음과 같다.
     - 1080p 프레임당 2-5분
     - 약 3500x3500 px 히어로 패널 12-30분
     - 4961x7016·128spp 전체 A2 프레임 35-85분
   - 하룻밤 배치 한 번에 들어간다.
   - 스크립트: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane-blender-diorama/scripts/calib_render.py`
   - 출력: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane-blender-diorama/out/calib_cycles_128spp_1920_d1500.png`

3. **격차는 기하나 렌더링이 아니라 세트 드레싱이다**
   - 에이전트가 5분 만에 쓴 bpy 블록아웃(보정 이미지)만으로도 이미 폐허가 된 콜로세움으로 읽힌다.
   - 참조와 비교해 부족한 것: 블록별 색·베벨 변화, 풍화와 때, hypogeum 미로, 목재 아레나 가장자리, 식생, 소품, 사람.
   - 에이전트는 절차적 GN과 스캐터로 이것들을 만들 수 있다.
   - 시간을 잡아먹는 일은 에셋 고르기·데시메이트·배치, 사람 포즈 잡기, 아트 디렉션 패스다.

4. **Blender 5.2 Geometry Nodes는 이제 폐허의 어려운 부분을 절차적으로 처리할 수 있다**
   - 로컬에서 존재를 확인한 노드 타입은 다음과 같다.
     - GeometryNodeMeshBevel(5.2 신규, 모따기된 석재 블록)
     - GeometryNodeMeshBoolean
     - SDF 그리드 노드: MeshToSDFGrid, SDFGridBoolean, SDFGridOffset, SDFGridFillet, GridToMesh(침식되고 깨진 모서리, 균열 기하)
     - Repeat zones, Lists, Geometry Bundles
     - DistributePointsInVolume(콘크리트 단면의 골재)
     - Raycast
   - 번들된 CC0 Essentials는 Scatter on Surface, Randomize Transforms, Array, Displace Geometry, Curve to Tube를 더한다.
   - 컴포지터 쪽으로는 Vignette, Film Grain, Split Toning, Chromatic Aberration을 더한다.

5. **AI 참조보다 정확하다**
   - 파라메트릭 모델은 개수가 정확하다.
   - 예: 층당 80 베이, 아케이드 3층+attic, 188x156 m 타원, 판테온의 28개 coffer 5단과 약 8-9 m의 oculus, 링 기초 컷어웨이 깊이.
   - 교육용 포스터에서는 이 점이 중요하다.
   - Blender는 모든 랜드마크를 같은 axonometric 카메라·태양 각도·팔레트로 렌더한다. 그래서 6개 랜드마크의 일관성이 유지되고 203X 레이아웃의 요구에도 맞는다.
   - 이미지 생성기는 이 두 가지 모두 보장하지 못한다.

6. **출처가 깨끗한 로마 전용 에셋은 드물다**
   - 쓸 수 있는 CC0 출처는 다음과 같다.
     - Poly Haven
       - 텍스처: large_sandstone_blocks, white_sandstone_blocks_02, rock_embedded_concrete, stone_embedded_concrete, concrete_layers, rough_plaster_brick, cobblestone_large_01, patterned_cobblestone, brick_villa_floor 등
       - 모델: shrub_01-04, 바위, 고리버들 바구니, 나무 양동이·상자, 도자기 항아리 등
       - HDRI
     - ambientCG
     - Blender Human Base Meshes
     - MPFB2 출력물
     - Quaternius/Kenney 인물
   - Sketchfab의 로마 소품은 대부분 CC-BY 4.0이다. **인쇄에는 사용 가능**하지만 포스터에 크레딧 블록이 필요하다.
   - 피해야 할 것은 다음과 같다.
     - 'Il Colosseo'(ariadams): Google Earth Studio로 만들었다고 명시되어 있어 CC-BY 표기를 믿을 수 없다.
     - CMBC Colosseum/Pantheon 모델: 출처가 없다.
     - 모든 **NC/ND(비상업·변경금지)** 항목: sowillo plaques, Miniatur Wunderland Pompeii 스캔(남의 저작권이 있는 미니어처를 스캔한 것이기도 하다).
     - 'Ruined Aqueduct Arches Segment': 2026년 업로드이고, 설명이 AI가 쓴 글처럼 읽히며, 출처가 불분명하다.

7. **한국 거주 사용자에게 걸리는 라이선스 함정**
   - Tencent Hunyuan3D 2.0과 2.1 라이선스는 'DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA'라고 명시한다(두 저장소의 LICENSE에서 확인). 즉 **한국은 적용 지역에서 제외**된다.
   - 인쇄 포스터에 Hunyuan3D 가중치나 출력물을 쓰지 않는다. MCP generate_3d 도구 뒤에 있는 Hunyuan 옵션도 포함되며, 이 옵션은 **유료·크레딧 기반 서비스**이기도 하다.
   - Blender, GPL 애드온, GPL MCP 애드온은 렌더 결과물에 제약을 주지 않는다.
   - MPFB는 출력물이 사용자 소유라고 명시한다(CC0 에셋).
   - BlendKit(옛 BlenderKit)의 Royalty-Free 에셋은 렌더에서의 **상업적 사용을 허용**하지만, 원본 에셋을 재판매하는 것은 허용하지 않는다.

8. **M1/16 GB에서 지킬 규칙**
   - 미니어처 스케일에는 4-8K 텍스처가 필요 없다. 1K-2K를 쓴다. 비압축 8-bit 4K RGBA 텍스처는 Cycles에서 약 64 MB, 2K는 약 16 MB다.
   - 포토그래메트리 스캔은 1-9M 면에서 약 200-500k로 데시메이트한다. 포스터에서 각 랜드마크의 폭은 약 2000-3500 px뿐이기 때문이다.
   - 돌·사람·식생은 인스턴싱한다.
   - Blender 5.2는 메모리를 줄이는 Cycles Texture Cache(.tx 타일)를 추가했다. 다만 릴리스 노트에 Metal에서 동작하는지가 나와 있지 않으므로 테스트해야 한다.
   - Blender MCP 라이브 세션과 헤드리스 렌더를 동시에 돌리지 않는다.

9. **에이전트로 구동하기 쉽다**
   - `blender -b --factory-startup --python script.py -- args`가 이 장비에서 헤드리스로 동작했다.
   - MCP for Blender 애드온(ahujasid, MIT, 옛 이름 blender-mcp; 애드온 bl_info v1.8 설치, PyPI 서버 2.1.9)이 이미 연결되어 있다. execute_blender_code와 look 스크린샷으로 생성-렌더-비평 루프를 돌릴 수 있다.
   - 대화형 아트 디렉션에는 MCP를, 재현 가능한 키트 빌드와 최종 렌더에는 헤드리스 bpy를 쓴다.
   - MCP 텔레메트리는 끈다(이를 위한 도구가 있다).
   - Blender Lab의 공식 MCP(v1.0.3, Blender 5.1+)는 장면 검사가 중심이다. 그 강화 포크인 bpy-dev/blender-mcp는 저장된 .blend 파일에 쓰는 헤드리스 _for_cli 도구를 더한다.

10. **미니어처 룩 레시피(참조의 따뜻하고 장난감 같은 GI를 재현)**
    - 카메라 고도를 약 30-35도로 높게 잡는다.
    - 먼 거리에서 근-등각 장초점 렌즈(200-300 mm)를 쓰거나 직교 카메라를 쓴다. Pohlke 확장은 진짜 axonometric/oblique 투영을 만든다.
    - 태양 램프 각도를 5-10도로 해서 접촉 그림자를 부드럽게 하고, Poly Haven의 따뜻한 하늘 HDRI를 낮은 강도로 더한다.
    - AgX + Base Contrast를 쓴다(5.0부터 ACES 2.0도 쓸 수 있다).
    - 물리적으로 스케일된 DOF를 쓴다. 장면을 1:500으로 줄여 매크로 f-stop을 쓰거나, 1:500 미니어처에 해당하는 조리개를 계산한다. 직교 카메라에서 DOF가 기대대로 동작하는지 확인하거나, 대신 장초점 원근 카메라를 쓴다.
    - 은은한 AO 패스를 곱하기로 얹는다.
    - 섀도 캐처 뒤에 무광의 따뜻한 바탕색을 둔다.
    - 멀티레이어 EXR 패스를 출력한다: Mist/Z, Normal, AO, Diffuse Color, Cryptomatte object/material, Object Index, Shadow catcher, alpha.
    - 이 패스들로 Figma에서 203X 스타일 지시선 합성을 하고, 나중에 ControlNet depth/lineart를 이용한 AI 보정도 한다.

11. **판정**
    - 이 경로 하나만으로 참조의 구도·조명·구조적 깊이·석재별 변화를 맞출 수 있고, 정확도와 일관성에서는 참조를 넘어선다.
    - 약점은 6개 랜드마크 전체에서 참조의 소품·인물 밀도를 합리적인 시간 안에 맞추는 일이다. 사람의 아트 디렉션을 약 2-3일 더하지 않으면, 에이전트 단독 작업은 참조 풍부함의 약 70%에 머물 가능성이 크다.
    - 권장 구성
      - Blender를 기하·카메라·조명의 기준(source of truth)으로 삼는다.
      - 선택적으로 저강도 AI 디테일 패스를 더한다: denoise 약 0.25-0.4, Blender 패스에서 만든 ControlNet depth+lineart, 끝난 뒤 아치 개수 확인.
      - 그다음 300 dpi로 업스케일한다.
    - 균열 치유 단면과 기초 단면은 Blender로만 만든다(도해적 정밀도).

---

## 3. 권장 파이프라인

1. **키트 먼저 만들기(한 번만 구축, 약 1.5-2 에이전트-일)**
   - 헤드리스 bpy에서 에이전트가 GN 노드 그룹으로 'Roman miniature kit'를 작성한다.
     - stone-coursing: 블록별 크기 지터, Mesh Bevel, 인스턴스별 색조·거칠기·때 속성
     - 타원형/원형 베이 배열: 층당 정확히 80 베이, 오더와 attic
     - 방사형 벽과 볼트 복도
     - cavea 계단
     - hypogeum 격자
     - 폐허 마스크: 노이즈+평면 절단, SDF Offset/Boolean 침식, Cell Fracture 잔해
     - coffer 돔: 5x28 coffer, oculus
     - specus 수로가 있는 수도교 아케이드
     - 항구 방파제(mole)
     - 콘크리트 단면 생성기: DistributePointsInVolume 골재, 석회 덩어리(lime clasts), 균열 SDF, 방해석 충전(calcite infill)
   - 여기에 공유 재질을 더한다: Poly Haven/ambientCG CC0 1-2K, 미니어처 스케일에 맞게 UV 스케일 조정.
   - 공유 조명 리그를 더한다: 각도 5-10도의 태양, 따뜻한 Poly Haven 하늘, AgX Base Contrast, 따뜻한 무광 받침+섀도 캐처, 모든 패널에 쓰는 axonometric/장초점 카메라 프리셋 하나.

2. **랜드마크별 작업**
   - 실제 치수로 키트에서 블록아웃한다.
   - 기초 단면과 돔 단면용 컷어웨이 boolean을 적용한다.
   - 폐허·풍화 패스를 적용한다.

3. **GN 스캐터로 드레싱(Essentials Scatter on Surface, BagaPie 또는 OpenScatter)**
   - 식생: CC-BY 사이프러스·올리브와 절차적 MTree 변형, Poly Haven 관목·잔디
   - 소품: CC-BY 크레인, 비계, 암포라, 기둥; CC0 바구니·양동이
   - 인물: Quaternius CC0 포즈 군중과 포즈를 잡은 MPFB2 CC0 노동자, GN 속성으로 인스턴스마다 재채색

4. **아트 디렉션 루프**
   - MCP for Blender로 빠르게 반복한다(execute_blender_code 실행 후 EEVEE로 look).
   - 같은 스케일의 참조 크롭과 비교한다.

5. **최종 렌더**
   - 헤드리스 Cycles Metal 렌더(128spp adaptive + OIDN). 히어로 패널당 약 12-30분, 밤새 돌린다.
   - Mist/Z, Normal, AO, Diffuse Color, Cryptomatte, Object Index, alpha, shadow catcher를 담은 멀티레이어 EXR을 출력한다.
   - 선택적으로 Grease Pencil Line Art 외곽선을 더한다.

6. **선택적 AI 디테일 패스(다른 레인 담당)**
   - 이 패스들에서 만든 ControlNet depth+lineart로 저강도 img2img/edit를 한다.
   - 그다음 엣지 마스크를 Blender lineart와 비교해 개수와 실루엣이 살아남았는지 자동으로 확인한다.
   - 그다음 300 dpi로 업스케일한다.

7. **203X 레이아웃 합성**
   - Cryptomatte·객체 마스크와 내보낸 3D→2D 라벨 앵커(world_to_camera_view)를 써서 Figma의 203X 레이아웃에 패널을 합성한다.
   - Sketchfab API의 라이선스 필드로 CC-BY 크레딧 블록을 자동 생성한다.
   - **NC/ND 에셋이나 지역 제외 에셋**이 하나라도 있으면 빌드를 실패시킨다.

- 균열 치유 단면과 기초 단면은 도해 정밀도를 위해 순수 Blender로 유지한다.

---

## 4. 랜드마크당 작업량 추정

에이전트가 구동하고 사람이 아트 디렉션을 검토하는 방식이다. 일회성 공유 키트(GN 생성기, 재질, 조명·카메라 리그, 인물 라이브러리, 스캐터 설정)는 약 1.5-2 에이전트-일이며 콜로세움 예산에 포함했다.

| 랜드마크 | 에이전트 시간 | 사람 아트 디렉션 | 비고 |
|---|---|---|---|
| 콜로세움(폐허, hypogeum, 콘크리트 링 기초 컷어웨이, 드레싱한 광장) | 2-3일 | 0.5-1일 | 히어로 렌더당 Cycles 15-30분 |
| 폼페이 hot-mixing 공사 현장(석회 가마, 모르타르 구덩이, 크레인, 비계, 포즈 잡은 노동자 30-60명) | 1.5-2.5일 | 약 0.5일 | 인물 포즈 잡기가 병목 |
| 판테온 돔 컷어웨이(5x28 coffer, oculus, 위로 갈수록 가벼워지는 골재 띠, 포르티코) | 0.5-1일 | | |
| 수도교 상부 수로 컷어웨이(specus, cocciopesto 라이닝) | 약 0.5일 | | |
| 포르투스 항구(육각형 내항, 방파제, 배, 물) | 1-1.5일 | | |
| 균열 치유 콘크리트 단면(절차적 SDF/볼륨 골재와 균열) | 약 0.5일 | | |

- 합계: 6개 패널을 참조 풍부함의 약 80-90% 수준으로 만드는 데 약 6-9 에이전트-일과 사람 2-3일.
- 렌더링: M1 로컬에서 약 하룻밤 추가(패널 3000-3500 px; 전체 A2 Cycles 프레임 하나는 35-85분).
- 사람의 아트 디렉션 없이 에이전트만 돌리면 약 3-4일에 끝나지만, 참조의 소품·인물 밀도는 약 60-70%에 그친다.

---

## 5. 실제로 실행한 검증·시험과 결과

### 이번 조사에서 실행·확인한 것

- **보정 렌더(calib_render.py, 헤드리스)**
  - 환경: Blender 5.2.2, 7코어 M1 GPU의 Cycles Metal, OIDN, adaptive sampling.
  - 장면: 타원형 3층·80베이 아케이드 프록시, 단색 재질, 태양+월드 조명, 직교 카메라.
  - 결과: 960x540/64spp 8.6 s. 1920x1080/128spp는 인스턴스 약 63k개에서 37.9 s, 인스턴스 자갈 약 1.18M개에서 53.1 s. EEVEE 1080p는 같은 두 장면에서 3.3 s와 15.0 s. 최대 RAM 3.5-4.7 GB.
  - 보정 장면 빌드 시간은 0.5 s였다.
  - 첫 Metal 커널 컴파일은 몇 분 걸릴 수 있는데, 이 장비에서는 이미 캐시되어 있었다.
  - 출력: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane-blender-diorama/out/calib_cycles_128spp_1920_d1500.png`
- **헤드리스 실행 확인**: `blender -b --factory-startup --python script.py -- args`가 동작했다. 헤드리스 렌더 3회가 총 약 1분 걸렸다. Blender는 `/opt/homebrew/bin/blender`에 이미 설치되어 있다.
- **GN 노드 타입 로컬 확인**: GeometryNodeMeshBevel, GeometryNodeMeshBoolean, MeshToSDFGrid, SDFGridBoolean, SDFGridOffset, SDFGridFillet, GridToMesh, Repeat zones, Lists, Geometry Bundles, DistributePointsInVolume, Raycast가 존재한다.
- **Essentials 에셋 로컬 확인**: datafiles/assets에서 GN·컴포지터·헤어 노드 그룹을 확인했다. 같은 위치의 LICENSE 파일에서 CC0-1.0을 확인했다.
- **MCP for Blender 연결 확인**: 사용자의 Blender 5.2 애드온에 'MCP for Blender'(bl_info v1.8)가 설치되어 있고 연결되어 있다. PyPI 서버는 2.1.9다.
- **Hunyuan3D 라이선스 원문 확인**: Hunyuan3D 2.0과 2.1 두 저장소의 LICENSE에서 EU, 영국, **한국 제외** 문구를 확인했다.
- **참조 이미지 파일 점검**: 크기 1376x768(Gemini 3 계열 16:9 1K 출력과 일치). APP/EXIF/XMP/C2PA 세그먼트 없음(CDN이 제거). Last-Modified와 파일명 타임스탬프는 2026-02-10.
- **Poly Haven API 조회**: 오늘 기준 모델 521개, 텍스처 869개. pine_tree_01은 17.4M 폴리곤.
- **Sketchfab 라이브 API 확인(2026-10-18)**: 소품 모델들의 라이선스와 폴리곤 수를 확인했다.

### 원문이 제시한 스모크 테스트

첫 항목만 이미 검증되었고, 나머지는 실행 절차와 기대값 형태로 제시되었다.

1. **보정 재실행(가벼움, 이미 검증됨)**
   - 명령: `RX=1920 SPP=128 DENS=1500 /opt/homebrew/bin/blender -b --factory-startup --python /private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/lane-blender-diorama/scripts/calib_render.py -- <outdir>`
   - 기대값: Cycles 약 53 s, EEVEE 약 15 s, 최대 RSS 약 4.7 GB.
2. **GN 콜로세움 생성기 정확도 테스트(헤드리스)**
   - bays=80, tiers=3+attic으로 빌드한다.
   - 층별로 평가된 인스턴스 수가 80인지, attic에 아치가 아니라 벽기둥(pilaster)이 있는지 assert한다.
   - 960x540 EEVEE 확인 이미지를 렌더해 실루엣을 콜로세움 평면도와 비교한다.
3. **석재별 디테일 테스트**
   - Mesh Bevel 블록, 인스턴스별 색조·때, SDF로 침식한 상단을 갖춘 3x3 베이 폐허 구간 하나를 만든다.
   - 포스터에서 실제로 가질 픽셀 스케일(베이당 약 300 px)로 렌더한다.
   - `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/ref-model-level/crop-front.png`와 나란히 놓고 비교한다.
4. **메모리 테스트**
   - CC-BY 스캔 3개를 가져온다(예: Colosseum Facade 221k, Roman old arch Pompeii 221k, 400k로 데시메이트한 Pantheon Interior).
   - 텍스처를 2K로 줄이고, 인스턴스 돌 1M개를 더한 뒤 1080p Cycles로 렌더한다.
   - 기대값: 최대 RSS 10 GB 미만.
   - Cycles 5.2 Texture Cache를 켠 경우와 끈 경우를 반복해 Metal에서 도움이 되는지 본다.
5. **미니어처 DOF 테스트**
   - 같은 장면을 (a) 직교 카메라+DOF, (b) 1:500 스케일로 계산한 f-stop의 250 mm 원근 카메라로 렌더한다.
   - 직교 DOF가 렌더되는지 확인한 뒤, 참조의 부드러운 흐림 감쇠에 가장 가까운 룩을 고른다.
6. **패스 내보내기 테스트**
   - Mist, Normal, AO, DiffCol, CryptoObject, IndexOB, shadow catcher가 담긴 멀티레이어 EXR을 렌더한다.
   - bpy(`bpy.data.images.load(...).layers`) 또는 `oiiotool --info`로 레이어를 확인한다.
   - 객체 5개의 3D→2D 라벨 앵커를 Figma용 JSON으로 내보낸다.
7. **MCP 루프 테스트**
   - mcp-for-blender로 에이전트에게 10x10 m 광장(자갈, 노점 2개, 암포라 6개, 사람 12명, 사이프러스 3그루)을 드레싱하게 하고, 단계마다 look을 쓰게 한다.
   - 아트 디렉터가 받아들일 결과가 나올 때까지의 반복 횟수와 소요 시간을 잰다.
8. **라이선스 게이트 테스트**
   - 가져온 모든 에셋에 대해 `https://api.sketchfab.com/v3/models/<uid>`를 조회해 CC-BY 크레딧 블록을 쓰는 스크립트를 만든다.
   - **NC/ND 라이선스**, Google Earth 파생 태그·설명, Hunyuan3D로 생성한 메시가 하나라도 있으면 0이 아닌 코드로 종료한다.

---

## 6. 후보 도구 표

적합도 높은 순으로 정렬했다. 같은 점수 안에서는 원문 순서를 따랐다. 각 후보의 적합 이유와 모든 근거 URL은 표 아래 6-1절에 있다.

| 이름 | 단계 | 하는 일 | 적합도(1~5) | 라이선스 | 상업·인쇄 사용 | M1 로컬 | 클라우드 | 에이전트 구동 | 유지보수 | 주의사항 | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Blender 5.2.2 LTS + Geometry Nodes (핵심 모델링 엔진) | 모델링 | 6개 랜드마크 전부를 파라메트릭·절차적으로 모델링: 타원형 베이 배열, 링 벽, 볼트 복도, cavea 계단, hypogeum 격자, 폐허 마스크, coffer 돔, 수도교 specus, 항구 방파제, 콘크리트 단면. 5.2는 Mesh Bevel 노드, Lists, Geometry Bundles, 더 빠른 EEVEE 인스턴싱, Cycles 텍스처 캐시를 추가. 5.0은 SDF/볼륨 그리드 노드, Bundles/Closures, ACES 2.0을 추가 | 5 | GPL-2.0-or-later(애플리케이션). 렌더·출력물은 사용자 소유, 제약 없음 | **가능** | **가능**. `/opt/homebrew/bin/blender`에 이미 설치. 보정 장면 빌드 0.5 s. 일반 디오라마는 16 GB 통합 메모리 중 약 3-8 GB RAM | 필요 없음. 원하면 SheepIt(무료 커뮤니티 팜, Blender 5.2 지원 명시) 또는 RunPod/Vast Blender 컨테이너(**유료**) | 가능: 전체 bpy API, 헤드리스 'blender -b --python', MCP execute_blender_code | 5.2 LTS 2026-07-14 출시, 2028년 7월까지 유지 | 5.2에서 GN 모디파이어 속성 Python API와 Compare·Random Value 노드의 소켓 ID가 바뀌어, 예전 GN 스크립트나 에셋은 수정이 필요할 수 있음. GN 도구를 담은 에셋 파일은 다시 저장해야 함 | https://www.blender.org/download/releases/5-2/ |
| Cycles (Metal GPU) + OIDN: 최종 미니어처 룩 렌더러 | 렌더 | 경로 추적 GI, 부드러운 태양·하늘, 접촉 차폐, 틸트시프트 룩용 DOF, AgX/ACES 뷰. 합성과 ControlNet용 멀티레이어 EXR 패스(Mist/Z, Normal, AO, Diffuse Color, Cryptomatte, Object Index, Shadow Catcher, alpha) 출력 | 5 | Apache-2.0(Cycles), Blender에 포함 | **가능** | **가능**, 실측: 단순 프록시에서 1080p/128spp 38-53 s(인스턴스 1.18M, 최대 3.3-4.7 GB). 참조 수준 장면 추정: 1080p 2-5분, 3500x3500 패널 12-30분, 전체 A2 4961x7016 35-85분 | SheepIt(무료; 장면이 자원봉사자 기기로 가므로 공개로 간주) 또는 **유료** GPU 임대 | 가능(bpy로 scene.cycles.* 설정; 헤드리스 렌더) | 활발(Blender의 일부) | 5.2 Texture Cache는 Metal 지원을 문서화하지 않았으므로 테스트할 것. 첫 Metal 커널 컴파일은 몇 분 걸릴 수 있음(여기서는 캐시되어 있었음). 텍스처는 1-2K 유지 | https://developer.blender.org/docs/release_notes/5.2/cycles/ |
| MCP for Blender (ahujasid/mcp-for-blender, 옛 blender-mcp) | 오케스트레이션 | Claude에서 라이브 Blender로 잇는 소켓 브리지: Python 실행, 자기 비평용 다각도·카메라 'look' 스크린샷과 렌더, Poly Haven/Sketchfab/Poly Pizza 가져오기, AI 3D 생성(Tripo, Hyper3D Rodin, Hunyuan3D, 모두 프리미엄/**유료**) | 5 | MIT | 도구 자체는 **가능**. 생성된 3D는 제공자에 따라 다름. Hunyuan3D 라이선스는 **한국 제외** | **가능**(가벼움) | 프리미엄 AI-3D 생성은 **유료** | 가능(그것이 목적) | 매우 활발: 31.4k stars, 2026-10-06 push, PyPI mcp-for-blender 2.1.9 | 사용자 Blender에서 임의 코드를 실행하므로 자주 저장할 것. 텔레메트리가 있으므로 끌 것. Sketchfab 가져오기는 API 키 필요. 라이선스 확인 없이 포스터 에셋에 generate_3d를 쓰지 말 것. 한국 사용자는 Hunyuan 회피 | https://github.com/ahujasid/mcp-for-blender |
| 헤드리스 bpy 스크립팅 (blender -b --factory-startup --python) | 오케스트레이션 | UI 없이 재현 가능한 키트 빌드(콜로세움·판테온 생성기), 배치 렌더, 패스 내보내기. 이번 조사의 보정을 이 방식으로 실행함 | 5 | GPL(Blender) | **가능** | **가능**(확인: 헤드리스 렌더 3회, 총 약 1분) | 같은 스크립트를 **유료** GPU 호스트의 Linux 컨테이너에서 실행 | 가능 | 활발 | 라이브 MCP Blender가 바쁠 때 무거운 헤드리스 렌더를 돌리지 말 것(16 GB 공유) | https://docs.blender.org/api/current/ |
| Poly Haven (텍스처, HDRI, 모델) | 에셋 | API로 받는 CC0 PBR 텍스처와 모델. 관련 텍스처: large_sandstone_blocks, white_sandstone_blocks_02, castle_brick_07, old_stone_wall, rock_embedded_concrete, stone_embedded_concrete, concrete_layers, rough_plaster_brick, cobblestone_large_01, patterned_cobblestone, brick_villa_floor, cracked_concrete. 모델: shrub_01-04, boulder_01, stone_01, wicker_basket_01/02, wooden_bucket_01/02, wooden_crate_01/02, ceramic_pot, planter_pot_clay, grass_medium_01/02. 따뜻한 하늘 HDRI도 있음 | 5 | CC0-1.0 | **가능** | **가능**(1K-2K 해상도에서). 수백만 폴리곤 나무는 피할 것(pine_tree_01은 17.4M 폴리곤) | 해당 없음 | 가능(api.polyhaven.com; MCP import_asset) | 활발(오늘 API 기준 모델 521개, 텍스처 869개) | 텍스처가 실제 스케일이므로 미니어처 가독성을 위해 UV를 스케일할 것. 로마 전용 소품은 적음 | https://polyhaven.com |
| EEVEE (5.2): 빠른 룩 개발과 미리보기 렌더 | 렌더 | 화면 공간 레이 트레이싱을 갖춘 래스터 렌더러. 즉각적인 아트 디렉션 루프용이며, 단순한 패널은 최종본에도 쓸 수 있을 수 있음 | 4 | GPL(Blender의 일부) | **가능** | **가능**, 실측 1080p 프레임당 3.3-15 s, 최대 RAM 4.7 GB | 해당 없음 | 가능 | 활발. 5.2는 인스턴스가 많을 때 약 2배 빠르고, 디더링과 스크린 트레이싱 개편을 추가 | AO와 GI가 물리적으로 덜 정확해 밀도 높은 미니어처에서 드러남 | https://www.blender.org/download/releases/5-2/ |
| Blender Essentials 에셋(번들, CC0): GN·합성·헤어 노드 그룹 | 스캐터 | 로컬 datafiles/assets에서 확인한 번들 노드 그룹: GN Scatter on Surface, Randomize Transforms, Random Rotation, Array, Instance on Elements, Displace Geometry, Curve to Tube, Box/Sphere Selection, Smooth by Angle. 컴포지터 Vignette, Film Grain, Split Toning, Chromatic Aberration, Sensor Noise. 절차적 헤어 커브(잔디 덤불에 사용 가능) | 4 | CC0-1.0(datafiles/assets의 LICENSE 파일에서 확인) | **가능** | **가능**(이미 있음) | 해당 없음 | 가능(bpy.data.libraries.load로 노드 그룹 append) | 활발. 5.2는 Essentials를 온라인으로 호스팅 | 범용적임. 석재 coursing과 폐허 로직에는 여전히 맞춤 GN이 필요 | https://www.blender.org/download/releases/5-0/ |
| BagaPie (extensions.blender.org) | 스캐터 | GN 도구 50개 이상: 카메라 컬링이 되는 스캐터·페인트 스캐터, 아이비 생성기, 선/격자/원/커브 배열, 파라메트릭 벽·기둥·계단·바닥·울타리·보·타일, face-to-paving, boolean draw | 4 | GPL-3.0-or-later | **가능** | **가능** | 해당 없음 | 부분적(연산자는 bpy로 호출 가능, GN 그룹은 스크립트 가능) | v11.0.12, Blender 5.0+ 필요, Blender 5.2용 수정 포함 | 페이지에 가격이 명시되지 않았지만 공식 플랫폼에서 무료로 배포됨. 건축 프리셋은 로마식이 아니라 범용 | https://extensions.blender.org/add-ons/bagapie/ |
| MPFB2 (MakeHuman for Blender): 미니어처 인물 | 인물 | 리그·포즈·의상·스크립팅 API(script_samples)를 갖춘 파라메트릭 인간 생성기. 다양한 노동자·시민을 일괄 생성 | 4 | 코드 GPL-3.0. 번들 에셋 CC0-1.0. LICENSE.md 섹션 D: 출력물(내보내기, 렌더)에 권리 주장 없음 | **가능** | **가능** | 해당 없음 | 가능(Python API) | 활발: 확장 2.0.18, 저장소 2026-10-13 push | 로마 의상이 번들되지 않으므로 단순한 튜닉·토가 프록시를 모델링할 것. 많은 인물의 포즈를 잡는 일이 느림. 포즈 라이브러리 재사용 | https://extensions.blender.org/add-ons/mpfb/ |
| Sketchfab CC-BY/CC0 소품: 폼페이 현장과 광장 드레싱 | 에셋 | Treadwheel Crane(sheffrator, CC-BY, 67.5k tris). Free Wooden Scaffolding Set(Just8, CC-BY, 47.8k faces). Toorlectra lime kiln(galway3d, CC0, 78.6k; 아일랜드 석회 가마, 형태 참고용). Roman furniture villa pack(AlbertGregl, CC-BY, 29.9k, 암포라 3개). Greek Amphoras Set 02(intervirtual, CC-BY, 37.5k). Cleveland Museum Neck Amphora(CC0, 113k). Doric Order Columns pack(oneironauticus, CC-BY, 21.7k). Broken Medieval column set(sousinho, CC-BY, 4.7k) | 4 | 모델별로 CC-BY 4.0(저작자 표시 필수) 또는 CC0 | **가능**(CC-BY는 크레딧 줄 필요, 지역 제외 없음) | **가능**(모두 120k 면 미만) | 해당 없음 | 가능(Sketchfab API 다운로드는 무료 계정과 토큰 필요; MCP Sketchfab 가져오기) | 라이브 API 2026-10-18 확인 | 크레인은 중세로 태그되어 있지만 설명에 로마 시대 사용도 언급됨. 정확성이 중요하면 polyspastos 형태로 개조. 그리스 암포라 형태는 로마 Dressel 유형이 아니므로 GN Curve to Mesh로 단순한 Dressel 1/2-4 프로파일을 모델링 | https://sketchfab.com/3d-models/treadwheel-crane-1129cebe176442d19aee2ef2459e1e1f |
| Sketchfab CC-BY 식생: Cypress tree (ElectroNick), Old olive tree (massive-graphisme) | 에셋 | 게임용 사이프러스(29.2k faces)와 오래된 올리브 나무(67.4k faces, 전부 Blender로 제작). GN으로 인스턴싱 | 4 | CC-BY 4.0 | **가능**(저작자 표시 조건) | **가능** | 해당 없음 | 가능 | 정적 업로드(2020, 2022) | 반복이 눈에 띄지 않도록 GN으로 크기·색조·회전을 바꿀 것 | https://sketchfab.com/3d-models/cypress-tree-249d8cb553a8469e9d645713f8e96ed1 |
| Blender 컴포지터 + 렌더 패스(Cryptomatte, Mist/Z, Normal, AO, Shadow Catcher) + Grease Pencil Line Art | 합성 | 객체별 마스크(지시선 앵커, 강조 콜아웃), 깊이 안개, AO 곱하기, 포스터 배경 위의 알파 섀도 캐처, 라인아트 외곽선을 위한 멀티레이어 EXR 패스. 5.2는 컴포지터 노드 35개와, 라벨 앵커 좌표를 내보낼 수 있는 3D→화면 공간 유틸리티를 추가 | 4 | GPL(Blender의 일부) | **가능** | **가능** | 해당 없음 | 가능(bpy로 뷰 레이어 패스와 컴포지터 노드 설정; bpy_extras.object_utils.world_to_camera_view로 3D→2D 투영) | 활발 | 색 파이프라인을 계획할 것: AgX/ACES로 렌더, 16-bit TIFF/EXR로 내보내기, 레이아웃 도구에서 CMYK로 변환 | https://www.blender.org/download/releases/5-2/ |
| Blender Lab MCP server(공식) / bpy-dev/blender-mcp 강화 포크 | 오케스트레이션 | 공식 경량 MCP(v1.0.3, Blender 5.1+): 장면 분석, 데이터 관계, 이름 변경, GN 트리 설명. bpy-dev 포크는 저장된 .blend 파일용 헤드리스 _for_cli 도구, 런타임 API 시그니처 조회, 타임아웃을 추가 | 3 | bpy-dev 포크: GPL-3.0. 공식 Lab 프로젝트 라이선스는 페이지에 명시되지 않음(projects.blender.org/lab/blender_mcp 확인 필요) | **가능**(도구만 해당) | **가능** | 해당 없음 | 가능 | 공식 v1.0.3. 포크는 'developer preview'(2026-10-06 push) | 안전장치 없이 LLM 코드를 실행함(공식 페이지가 경고). 같은 Blender 포트에 MCP 서버 두 개를 돌리지 말 것 | https://www.blender.org/lab/mcp-server/ |
| OpenScatter (joseph-wardle 커뮤니티 포크, GScatter 0.12 기반) | 스캐터 | 배치·크기·회전 효과와 프리셋을 갖춘 GN 스캐터링. Blender 4.2와 5.2에서 CI 테스트됨 | 3 | GPL-3.0-or-later | **가능** | **가능** | 해당 없음 | 부분적 | 커뮤니티 포크, 사용자 기반 작음(2026-10-11 push). GitMay3D/OpenScatter: 'no longer in development' | README에 번들 에셋 라이선스가 명시되지 않았으므로 번들 에셋을 쓰기 전에 확인할 것 | https://github.com/joseph-wardle/openscatter |
| Arch Generator (확장) | 모델링 | BMesh 생성기: 아치 프로파일 15종, 기둥 스타일 11종, 받침과 주두, 단일·다중 아치 배열 모드, springer 트림 | 3 | GPL-3.0-or-later | **가능** | **가능**(14.8 KB) | 해당 없음 | 가능(bpy로 연산자 호출) | v1.0.1, 2026-06-24 공개, Blender 5.0+ | 새롭고 작음(다운로드 3k). 출력 품질 미검증. GN이 아니라 파괴적 메시를 만듦 | https://extensions.blender.org/add-ons/arch-generator/ |
| Cell Fracture + Extra Mesh Objects (Wall Factory): 폐허 잔해와 블록 벽 | 모델링 | Cell Fracture: 메시를 보로노이로 부숴 잔해와 깨진 홍예석(voussoir)을 만듦. Extra Mesh Objects에는 개구부가 있는 성곽형 블록 벽인 Wall Factory가 포함 | 3 | GPL-3.0-or-later(둘 다) | **가능** | **가능** | 해당 없음 | 가능(연산자) | 커뮤니티가 유지하는 옛 번들 애드온(Cell Fracture 0.2.1; Extra Mesh Objects 0.4.1, 2026-04-01, 'limited support') | Wall Factory 옵션 구성(방사·돔 모드, 아치 개구부)은 기억에 의존한 것이며 페이지에서 확인하지 않음. UI에서 테스트할 것 | https://extensions.blender.org/add-ons/cell-fracture/ |
| Modular Tree (MTree) / Sapling Tree Gen: 절차적 나무 | 에셋 | 노드 기반(MTree 5.5.2)과 파라메트릭(Sapling 0.3.7) 나무 생성기. 실루엣을 조절할 수 있는 사이프러스·올리브 변형용 | 3 | GPL-3.0-or-later(생성된 나무는 사용자 출력물) | **가능** | **가능** | 해당 없음 | 부분적(MTree 노드 트리는 스크립트 가능; Sapling은 연산자) | MTree 확장 5.5.2(Blender 4.3.1+, 관리자 Brandyn-Britton; 옛 GitHub 저장소는 2024년 이후 정체). Sapling 0.3.7(Blender 4.4+) | 사이프러스는 맞춤 조정이 필요. 미니어처 스케일에서는 단순한 GN 원뿔 외형+잎 덩어리 스캐터가 더 좋아 보이고 렌더도 빠를 수 있음 | https://extensions.blender.org/add-ons/modular-tree/ |
| 장난감 스케일 인물 키트: Quaternius Background Posed Humans, Kenney Mini Characters, Blender Human Base Meshes | 인물 | Quaternius: 군중용으로 포즈를 잡은 무텍스처 인간 20개와 헤어스타일 8종(FBX/OBJ/Blend). Kenney Mini Characters: 장난감 인물(파일 25개). Blender Studio Human Base Meshes v1.4.1: 포즈용 CC0 베이스 메시 | 3 | Quaternius CC0; Kenney CC0; Human Base Meshes CC0 | **가능** | **가능**(매우 작음) | 해당 없음 | 가능(가져오기 + GN 인스턴싱) | 정적 팩. Human Base Meshes는 5.0과 함께 업데이트 | 현대 의복 실루엣이므로 튜닉 같은 셰이딩을 더할 것. Kenney의 양식화가 스캔 석재와 어울리지 않을 수 있음 | https://quaternius.com/packs/backgroundposedhumans.html |
| ambientCG + AmbientCG Material Importer / BlendKit(옛 BlenderKit) 무료 등급 | 에셋 | ambientCG: CC0 PBR 재질, GPL 확장으로 원클릭 가져오기. BlendKit: Royalty-Free 또는 CC0인 무료 모델 22k개와 재질 36k개를 담은 Blender 내 라이브러리 | 3 | ambientCG 에셋 CC0, importer GPL-3.0. BlendKit 에셋 RF(상업 사용 가능, 원본 에셋 재판매 불가) 또는 CC0, 애드온 GPL-2.0 | **가능**(RF: 렌더와 인쇄는 가능, 원본 에셋 재배포 금지) | **가능** | BlendKit Full Plan은 **유료**(필요 없음) | 부분적 | BlendKit은 2026년 리브랜딩. 애드온 저장소 2026-10-08 push | BlendKit 에셋 품질은 들쭉날쭉함. 에셋마다 라이선스 필드를 확인할 것 | https://extensions.blender.org/add-ons/ambientcg-material-importer/ |
| Sketchfab CC-BY 랜드마크 스캔: 참고용·텍스처 베이크 소스 | 에셋 | The Pantheon Interior(artfletch, CC-BY, 1.0M faces, 2026년 2월 본인 촬영 사진). Basilica of Maxentius(artfletch, CC-BY, 1.45M; 콘크리트 coffer 볼트). Colosseum Facade(Jeremy.Christopher, CC-BY, 221k 포토그래메트리). Anio Vetus aqueduct(juanbrualla, CC-BY, 1.65M). Remains of Roman Bridge of imperial aqueduct(tdr125, CC-BY, 273k). Roman old arch Pompeii와 Ruin stone wall in Pompeii(chabychab, CC-BY 스캔, 221k와 122k). Opus Reticulatum RAER(antonio_lg, CC-BY, 1.47M). Ancient roman road, Aquinum(Ars.archeo, CC-BY, 209k) | 3 | CC-BY 4.0 | **가능**(저작자 표시 조건) | **느림**: 1-1.6M 면 스캔은 하나씩은 잘 로드됨(텍스처 포함 각 약 0.5-1 GB). 여러 개를 합치기 전에 200-500k로 데시메이트하고 2K 텍스처 사용 | 해당 없음 | 가능(API 다운로드, bpy 데시메이트·베이크) | 정적 업로드 | 출처가 제각각임. 일부 드론 스캔은 제3자 영상으로 만들어졌으므로 artfletch, chabychab, 박물관 업로드를 우선할 것. 'Il Colosseo'(Google Earth Studio 파생), CMBC Colosseum/Pantheon(출처 없음), 'Roman Colosseum 3d Section'(9.3M faces, 출처 불명), 'Ruined Aqueduct Arches Segment'(2026, AI 제작 가능성), 모든 **NC/ND** 항목은 피할 것 | https://sketchfab.com/3d-models/the-pantheon-interior-5f35ab370082403e8c7829388f4e0c30 |
| Sketchfab CC-BY 선박·인물: 포르투스와 노동자 | 에셋 | Roman Liburna(agt14032013, CC-BY, 602k). Tiber Island Warship(OpusPoly, CC-BY, 500k). Roman Soldier T-pose(Andywoodhead, CC-BY, 281k; 미니어처에는 과함). Previz-Lowpoly Colosseum(neberkenezer, CC-BY, 199k; 블록아웃과 비례 확인 전용) | 3 | CC-BY 4.0 | **가능**(저작자 표시 조건) | **가능**(미니어처용으로 배는 약 50k로 데시메이트) | 해당 없음 | 가능 | 정적 업로드 | 이것들은 군함임. 포르투스 교통은 대부분 상선(corbita)이었으므로 맞춤 GN 선체가 필요할 수 있음. 모델마다 역사적 정확성을 확인할 것 | https://sketchfab.com/3d-models/roman-liburna-0d84c39a677e41e8964cc4f1ea51f504 |
| Pohlke (axonometry/oblique) + Isometric Scene Setup: 일관된 인포그래픽 카메라 | 제어(control) | Pohlke는 건축용 axonometric·oblique 투영을 설정. Isometric Scene Setup은 등각 카메라 리그를 만듦 | 3 | Pohlke GPL-3.0-or-later; Isometric Scene Setup GPL-3.0-or-later 및 MIT | **가능** | **가능** | 해당 없음 | 가능(또는 bpy로 카메라를 직접 설정) | Pohlke 2.1.0; Isometric Scene Setup 1.0.1(둘 다 Blender 4.2+) | oblique·직교 투영은 물리 기반 DOF를 복잡하게 만듦. 장초점 원근 카메라가 더 '미니어처'처럼 보일 수 있음 | https://extensions.blender.org/add-ons/pohlke/ |
| Gemini 3 계열 이미지 모델 / 'Nano Banana Pro' (대조군: 참조 이미지의 유력한 생성기) | AI-이미지 | 텍스트·이미지→이미지. 문서화된 16:9 1K 출력이 1376x768로 참조의 정확한 크기와 일치. 모든 출력에 SynthID 워터마크 | 3 | 독점 Google API 약관(OSS 아님) | Google 약관에 따름(현행 Gemini API 약관 확인 필요). 출력물에 SynthID | **불가**(API 전용) | **유료** API, Gemini 앱, 또는 Comfy Cloud 파트너 노드(**유료** 크레딧) | 가능(API) | 활발(문서 2026-10-09 업데이트) | OSS 범위 밖, 대조용. '참조 모델 수준'이 3D 에셋이 아니라 AI 이미지임을 보여줌 | https://ai.google.dev/gemini-api/docs/image-generation |
| Building Tools (ranjian0) | 블록아웃 | 직사각형 건물의 평면, 층, 문, 창, 지붕, 계단, 발코니 | 2 | MIT | **가능** | **가능** | 해당 없음 | 부분적 | v1.0.13(2025-05-16), README에 'Blender 4.0 compatible'. 2026-09-24 push | Blender 5.2 호환성 미검증. 모서리 요소는 90도에서만 동작(open issue #226) | https://github.com/ranjian0/building_tools |
| Sverchok / Archimesh | 모델링 | Sverchok: 노드 기반 파라메트릭 디자인 시스템. Archimesh: 방, 문, 창(실내) | 2 | Sverchok GPL-3.0; Archimesh GPL-2.0-or-later | **가능** | **가능** | 해당 없음 | 부분적 | Sverchok v1.4.0(2026-03-05)은 Blender 3.6-5.1 지원(5.2 미기재). Archimesh 확장 1.2.5 | Sverchok은 아직 5.2 인증이 안 됨 | https://github.com/nortikin/sverchok |
| Infinigen (Princeton): 절차적 바위, 잔디 덤불, 관목, 나무 | 에셋 | 대형 절차적 생성기 라이브러리(바위, 초원 덤불과 꽃, 단자엽식물, 나무, 지형). Blender UI에서 'minimal install'로 쓰거나 Python 모듈로 사용 | 2 | BSD-3-Clause | **가능**(BSD-3) | **느림/가능**: 문서에 Mac ARM 지원 명시. brew 의존성(cmake, llvm, open-mpi, libomp) 필요, 디스크 수 GB. 에셋을 한 번 생성해 내보낼 것 | Mac 설치가 실패하면 **유료** Linux GPU 머신에서 실행 | 가능(Python 모듈, 스크립트 생성) | 활발: 7.3k stars, v2.0.0a3 2026-10-08 | 자체 Blender 버전을 고정하므로 5.2에서 쓰려면 에셋을 .blend/.glb로 내보낼 것. 여유 디스크 17 GB로는 빠듯함. 작업 지시상 전역 설치 금지이므로 venv가 필요 | https://github.com/princeton-vl/infinigen |
| SheepIt Render Farm (선택적 무료 클라우드 렌더링) | 렌더 | Cycles와 EEVEE로 Blender 5.2를 지원하는 무료 커뮤니티 렌더 팜 | 2 | 무료 서비스(커뮤니티; 클라이언트 오픈소스) | **가능**(내 장면, 내 출력물) | 해당 없음(클라우드) | 무료(렌더해 주고 포인트 적립). **유료** 대안: RunPod/Vast GPU 컨테이너 | 부분적(웹 업로드) | 활발('free forever since 2007'; Blender 5.2 명시) | 장면 파일이 낯선 사람의 기기에서 렌더되므로 미공개·민감한 작업은 올리지 말 것. 텍스처는 pack할 것 | https://www.sheepit-renderfarm.com/ |
| Tencent Hunyuan3D 2.x (대조군: AI 3D 생성기; 한국에서 라이선스 제외) | AI-3D | 이미지 또는 텍스트→텍스처 메시. mcp-for-blender 프리미엄 generate_3d 뒤에 있는 백엔드 중 하나 | 1 | Tencent Hunyuan 3D 2.x Community License: Territory에서 EU, 영국, **한국 제외**(OSS 아님) | **불가**(한국 거주 사용자, **지역 제외**) | **느림/불가**(NVIDIA용으로 설계, M1 경로는 비현실적) | mcp-for-blender 프리미엄 또는 기타 유료 API 경유(**유료** 크레딧) | 가능(MCP generate_3d)하지만 회피 | 저장소 2025-10 push | 경고용으로만 수록. 다른 레인이 제안하는 다른 AI-3D 가중치에도 같은 확인을 적용할 것 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 |

### 6-1. 후보별 적합 이유와 근거 URL

#### Blender 5.2.2 LTS + Geometry Nodes (적합도 5, OSS)
- 적합 이유: 올바른 구조와, 랜드마크 간 일관된 카메라·조명을 보장하는 유일한 경로다. 정확한 개수로 참조의 구조적 깊이(여러 링, 실제 아치 깊이, 부서진 상단 윤곽)에 도달할 수 있다.
- 근거 URL
  - https://www.blender.org/download/releases/5-2/
  - https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/
  - https://www.blender.org/download/releases/5-0/
  - https://developer.blender.org/docs/release_notes/5.2/

#### Cycles (Metal GPU) + OIDN (적합도 5, OSS)
- 적합 이유: 참조의 따뜻한 GI·AO 룩은 전형적인 Cycles 미니어처 룩이며, 6개 패널 전부에서 재현할 수 있다.
- 근거 URL
  - https://developer.blender.org/docs/release_notes/5.2/cycles/
  - https://www.blender.org/download/releases/5-2/

#### MCP for Blender (적합도 5, OSS)
- 적합 이유: 이미 설치·연결되어 있다(사용자 Blender 5.2 애드온에 'MCP for Blender' bl_info v1.8). 아트 디렉션을 위한 에이전트의 빌드-확인-수정 루프를 가능하게 한다.
- 근거 URL
  - https://github.com/ahujasid/mcp-for-blender
  - https://pypi.org/project/mcp-for-blender/

#### 헤드리스 bpy 스크립팅 (적합도 5, OSS)
- 적합 이유: 결정적이고 버전 관리가 가능하며 MCP 세션과 병행할 수 있다. 최종 렌더와 회귀 검사(예: 층당 아치 개수 = 80 assert)에 가장 좋다.
- 근거 URL
  - https://docs.blender.org/api/current/

#### Poly Haven (적합도 5, OSS)
- 적합 이유: 라이선스 위험이 없는 핵심 재질 라이브러리다. rock_embedded_concrete와 concrete_layers는 로마 콘크리트 단면에 알맞다. 네이티브 MCP 가져오기가 있다.
- 근거 URL
  - https://api.polyhaven.com/assets?t=models
  - https://api.polyhaven.com/assets?t=textures

#### EEVEE (5.2) (적합도 4, OSS)
- 적합 이유: 이 장비에서 Cycles보다 5-15배 빠르다(보정에서 1080p 3.3 s와 15 s). MCP look과 함께 반복 작업하기에 충분하다. 최종 식생과 접촉 GI는 여전히 Cycles가 낫다.
- 근거 URL
  - https://www.blender.org/download/releases/5-2/

#### Blender Essentials 에셋 (적합도 4, OSS)
- 적합 이유: 설치 없이 쓰는 스캐터·인스턴스별 변화용 구성 요소이며, 전부 CC0다.
- 근거 URL
  - https://www.blender.org/download/releases/5-0/
  - https://www.blender.org/download/releases/5-2/

#### BagaPie (적합도 4, OSS)
- 적합 이유: 식생 스캐터, 포장(로마 도로·광장), 열주, 계단을 한 애드온으로 다루는 무료 GN 툴킷이다.
- 근거 URL
  - https://extensions.blender.org/add-ons/bagapie/
  - https://extensions.blender.org/api/v1/extensions/

#### MPFB2 (적합도 4, OSS)
- 적합 이유: 인물은 이미지 높이의 약 1%이므로 색 튜닉을 입힌 저렴한 프록시면 충분하다. MPFB 스크립팅으로 다양한 체형과 포즈(hot-mixing 노동자의 삽질·운반)를 얻는다.
- 근거 URL
  - https://extensions.blender.org/add-ons/mpfb/
  - https://github.com/makehumancommunity/mpfb2

#### Sketchfab CC-BY/CC0 소품 (적합도 4, 원문 분류상 OSS)
- 적합 이유: 참조가 보여주는 바로 그 소품 종류(크레인, 비계, 암포라, 부서진 기둥)다. 폴리곤 수가 낮아 16 GB에 맞다.
- 근거 URL
  - https://sketchfab.com/3d-models/treadwheel-crane-1129cebe176442d19aee2ef2459e1e1f
  - https://sketchfab.com/3d-models/free-wooden-scaffolding-set-de6d3cb59d0e4ef99103523ae22fbd88
  - https://sketchfab.com/3d-models/toorlectra-lime-kilm-example-one-0da9d13dae774ccfa732b888a8f0d990
  - https://sketchfab.com/3d-models/roman-furniture-roman-villa-pack-bc761cc327354c7394d120706f4d5417
  - https://sketchfab.com/3d-models/greek-amphoras-set-02-e114a15c0857459786e351d8a39f7036
  - https://sketchfab.com/3d-models/197016-neck-amphora-0bb2525bdd734bf69d5a7b2b051928ad
  - https://sketchfab.com/3d-models/doric-order-columns-asset-pack-e27b5b5c101c480dbf1a9781ae289155
  - https://sketchfab.com/3d-models/broken-medieval-column-set-962ed874cf9a4db5bc5405584c29b664

#### Sketchfab CC-BY 식생 (적합도 4, 원문 분류상 OSS)
- 적합 이유: 참조를 대표하는 두 가지 지중해 실루엣이며, 폴리곤 수가 미니어처에 알맞다.
- 근거 URL
  - https://sketchfab.com/3d-models/cypress-tree-249d8cb553a8469e9d645713f8e96ed1
  - https://sketchfab.com/3d-models/old-olive-tree-6328df8a0f214143a880a72b86db2ab4

#### Blender 컴포지터 + 렌더 패스 + Grease Pencil Line Art (적합도 4, OSS)
- 적합 이유: 3D 패널을 Figma의 203X 인포그래픽 레이아웃에 연결한다. 같은 패스가 AI 보정용 ControlNet에도 들어간다.
- 근거 URL
  - https://www.blender.org/download/releases/5-2/
  - https://www.blender.org/download/releases/5-0/

#### Blender Lab MCP server / bpy-dev/blender-mcp (적합도 3, OSS)
- 적합 이유: 런타임 API 조회와 저장된 파일에 대한 헤드리스 작업에 유용하다. ahujasid 쪽보다 에셋·렌더 도구가 적다.
- 근거 URL
  - https://www.blender.org/lab/mcp-server/
  - https://github.com/bpy-dev/blender-mcp

#### OpenScatter (적합도 3, OSS)
- 적합 이유: Geo-Scatter식 워크플로(잔디 덤불, 잔해, 군중)를 무료로 대체한다. 원조 GitMay3D/OpenScatter는 개발이 중단되었다.
- 근거 URL
  - https://github.com/joseph-wardle/openscatter
  - https://github.com/GitMay3D/OpenScatter

#### Arch Generator (적합도 3, OSS)
- 적합 이유: 에이전트가 인스턴싱할 아케이드 모듈(수도교 층, 콜로세움 베이, 개선문)을 빠르게 만든다. 로마 전용 오더는 확인되지 않았다.
- 근거 URL
  - https://extensions.blender.org/add-ons/arch-generator/

#### Cell Fracture + Extra Mesh Objects (적합도 3, OSS)
- 적합 이유: 폐허 상단과 무너진 베이에 쓸 깨진 모서리·잔해를 빠르게 만들어 GN SDF 침식을 보완한다.
- 근거 URL
  - https://extensions.blender.org/add-ons/cell-fracture/
  - https://extensions.blender.org/add-ons/extra-mesh-objects/
  - https://docs.blender.org/manual/en/4.1/addons/add_mesh/mesh_extra_objects.html

#### Modular Tree (MTree) / Sapling Tree Gen (적합도 3, OSS)
- 적합 이유: 참조는 사이프러스·올리브 실루엣에 기댄다. 절차적 나무는 사용자가 소유하는 CC0에 준하는 변형을 무한히 만든다.
- 근거 URL
  - https://extensions.blender.org/add-ons/modular-tree/
  - https://extensions.blender.org/add-ons/sapling-tree-gen/
  - https://github.com/MaximeHerpin/modular_tree

#### 장난감 스케일 인물 키트 (적합도 3, OSS)
- 적합 이유: 참조의 인물은 높이 약 1%의 장난감 같은 덩어리다. 포즈를 잡은 CC0 인물을 GN 'random colour' 속성으로 인스턴스마다 재채색하면 빠르게 맞출 수 있다.
- 근거 URL
  - https://quaternius.com/packs/backgroundposedhumans.html
  - https://kenney.nl/assets/mini-characters
  - https://www.blender.org/download/demo-files/

#### ambientCG + AmbientCG Material Importer / BlendKit (적합도 3, OSS)
- 적합 이유: 재질 공백(트래버틴, 응회암, opus reticulatum 비슷한 벽돌)과 일부 소품을 채운다.
- 근거 URL
  - https://extensions.blender.org/add-ons/ambientcg-material-importer/
  - https://www.blendkit.com/docs/licenses/
  - https://github.com/BlenderKit/Blendkit
  - https://www.cgchannel.com/2026/08/get-60000-free-3d-assets-for-maya-godot-and-rhino-from-blendkit/

#### Sketchfab CC-BY 랜드마크 스캔 (적합도 3, 원문 분류상 OSS)
- 적합 이유: 절차적 블록에 베이크할 진짜 표면 디테일과 풍화(데칼과 트림 텍스처)를 주고 비례를 확인하는 데 쓴다. 스캔 전체를 그대로 쓰면 깔끔한 미니어처 매스가 나오지 않는다.
- 근거 URL
  - https://sketchfab.com/3d-models/the-pantheon-interior-5f35ab370082403e8c7829388f4e0c30
  - https://sketchfab.com/3d-models/basilica-of-maxentius-6379df4cdb75480ba843129804060095
  - https://sketchfab.com/3d-models/colosseum-facade-rome-italy-d9a8a96e16534bdab76be23c1f2c45fc
  - https://sketchfab.com/3d-models/anio-vetus-aqueduct-italy-6236383efdf841b8bbb40799ea82eaec
  - https://sketchfab.com/3d-models/remains-of-roman-bridge-of-imperial-aqueduct-312647e7d0724356bc0983a229d3b67d
  - https://sketchfab.com/3d-models/roman-old-arch-pompeii-310e653aa0f543b7a6d098386197a16a
  - https://sketchfab.com/3d-models/ruin-stone-wall-in-pompeii-70077f93fdce46fab05e08d00f12b9b8
  - https://sketchfab.com/3d-models/opus-reticulatum-raer-f9659bf7146949ec9c7025a32778c205
  - https://sketchfab.com/3d-models/ancient-roman-road-for-metateca-project-69203c4908114b75aac2e0998c04952b
  - https://sketchfab.com/3d-models/il-colosseo-7cebd1c6d78847a19263ee9385741de1 (피해야 할 예시: Google Earth Studio 파생)

#### Sketchfab CC-BY 선박·인물 (적합도 3, 원문 분류상 OSS)
- 적합 이유: 포르투스에는 시대에 맞는 배가 필요한데, CC0 라이브러리에는 없다(Poly Haven의 배는 17세기 네덜란드 배).
- 근거 URL
  - https://sketchfab.com/3d-models/roman-liburna-0d84c39a677e41e8964cc4f1ea51f504
  - https://sketchfab.com/3d-models/tiber-island-warship-9aebf0b81f0949fc9ba47e2b14de4a0e
  - https://sketchfab.com/3d-models/roman-soldier-t-pose-free-download-61cd5cae148042c38048bff2bd206af3
  - https://sketchfab.com/3d-models/previz-lowpoly-colosseum-with-concept-textures-c1c2391478a34ba9a4c5f254c662fb30

#### Pohlke + Isometric Scene Setup (적합도 3, OSS)
- 적합 이유: 203X 레이아웃은 모든 랜드마크에 같은 투영을 쓰면 유리하다. 참조는 근-등각이다.
- 근거 URL
  - https://extensions.blender.org/add-ons/pohlke/
  - https://extensions.blender.org/add-ons/isometric-scene-setup/

#### Gemini 3 계열 이미지 모델 / 'Nano Banana Pro' (적합도 3, OSS 아님, 대조군)
- 적합 이유: 참조의 룩을 손쉽게 재현하지만, 개수를 틀리고 구조를 지어낸다(어긋난 아케이드 층, 지어낸 hypogeum). 6개 랜드마크의 일관성도 유지하지 못한다. 기준(source of truth)으로 쓰기보다 Blender 렌더 위에 얹는 보정·룩 목표로 쓰는 편이 낫다.
- 근거 URL
  - https://ai.google.dev/gemini-api/docs/image-generation
  - https://localbanana.io

#### Building Tools (ranjian0) (적합도 2, OSS)
- 적합 이유: 공사 현장 주변의 폼페이 주택·상점에만 쓸 만하다. 곡선형 로마 기념물에는 쓸모없다.
- 근거 URL
  - https://github.com/ranjian0/building_tools

#### Sverchok / Archimesh (적합도 2, OSS)
- 적합 이유: 여기서 Sverchok이 하던 일(coffer, 호)은 이제 네이티브 GN이 맡는다. Archimesh는 실내 지향이다. 완결성을 위해 수록했다.
- 근거 URL
  - https://github.com/nortikin/sverchok
  - https://extensions.blender.org/add-ons/archimesh/

#### Infinigen (Princeton) (적합도 2, OSS)
- 적합 이유: 고품질 자연 소품(참조 받침에 있는 잔디 덤불·바위 같은 것)을 만든다. 하지만 자체 Blender/bpy 버전을 갖는 무거운 설치이고, 몇 가지 에셋 유형만 쓰기에는 과하다.
- 근거 URL
  - https://github.com/princeton-vl/infinigen

#### SheepIt Render Farm (적합도 2, 원문 분류상 OSS)
- 적합 이유: 전체 A2 Cycles 프레임(로컬에서 각 35-85분)이 병목이 될 때만 필요하다.
- 근거 URL
  - https://www.sheepit-renderfarm.com/

#### Tencent Hunyuan3D 2.x (적합도 1, OSS 아님, 대조군)
- 적합 이유: 라이선스가 EU, 영국, 한국에는 적용되지 않는다고 명시하므로, 이 사용자의 인쇄 포스터에는 쓸 수 없다(**한국 지역 제외**).
- 근거 URL
  - https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
  - https://github.com/Tencent-Hunyuan/Hunyuan3D-2
