# 1차-B·C 조사 보고서: 벡터 편집기와 코드 기반 SVG

로마 콘크리트를 주제로 한 A2 세로 인포그래픽 포스터를 위해 오픈소스 도구·플러그인·스킬·하네스를 찾은 조사 결과다. 정보 디자인 벤치마크는 한국 스튜디오 203X의 포스터(베이징, 신문 제작 과정)이고, 2.5D/3D 모델의 수준 기준은 사용자가 준 아이소메트릭 미니어처 콜로세움 디오라마 이미지다.

> **읽기 전에**
> - 원문에 나오는 VTracer 단계, 자동 트레이싱, 트레이스 노이즈(색 조각, 밝은 점), 리뷰어 지적 사항은 모두 **사용자가 폐기한 이전 작업**(래스터 이미지를 트레이싱하던 이전 파이프라인)에 관한 것이다.
> - 203X 원본 크롭은 현재 `docs/references/assets/203x/originals/`에 있다.
> - 두 레인은 투영 기준을 다르게 적었다. B 레인은 "203X 베이징 크롭과 맞는 30° 트루 아이소메트릭"을, C 레인은 "elevation 30° / azimuth 45°, 즉 203X 포스터가 쓰는 2:1 다이메트릭"을 권한다. 아래에는 각 원문대로 옮겼다.

---

# 1부. B 레인: OSS 벡터 편집기와 아이소메트릭 드로잉 플러그인·확장

조사 범위: 203X 품질의 결과물을 손으로 또는 반자동으로 만들기 위한 OSS 벡터 편집기와 아이소메트릭 드로잉 플러그인·확장.

## 1.1 한눈에 보는 결론

- 유지보수 중인 OSS 편집기 가운데 여섯 요구사항을 한꺼번에 충족하는 것은 Inkscape 1.4.4뿐이다. 스냅되는 축측 그리드, 3D Box 도구, 헤드리스 불리언, 심볼·클론, 편집 가능한 한글 텍스트, PDF/SVG 내보내기, inkex와 CLI를 통한 에이전트 구동을 모두 갖췄다.
- 트레이싱 없이 기하로 가는 경로가 있다. 내장 3D Polyhedron 확장(OBJ를 면별 평면 음영 패스로 변환), 평면 투영 행렬(jdhoek 확장 또는 직접 적용), 헤드리스 path 액션 정리를 조합하면 된다.
- 이 Mac에서는 Inkscape MCP보다 Bash로 Inkscape CLI와 inkex 스크립트를 돌리는 쪽이 확실하다. MCP의 라이브 모드는 D-Bus, 즉 Linux 중심이다.
- Penpot, Graphite, Krita 등은 아이소메트릭 아트 본작업에 맞지 않는다. 인쇄용 CMYK/PDF-X는 Scribus 1.6.6로 넘기는 편이 안전하다.
- 상용 도구 중에서는 Affinity가 '활성 평면 위에 직접 그리기'로 가장 좋은 UX를 준다(무료지만 OSS 아님). 이 기능을 가진 OSS 도구는 없다.

## 1.2 핵심 발견

1. **Inkscape 1.4.4(2026년 5월)가 여섯 요구사항을 모두 충족하는 유일한 유지보수 중인 OSS 편집기다.** 갖춘 기능은 다음과 같다.
   - 스냅되는 축측(axonometric) 그리드. Angle X/Angle Z로 설정하며, 1.4부터는 각도 또는 높이:너비 비율로 지정할 수 있다.
   - 소실점을 무한대로 두고 각도를 210/270/330으로 맞추면 진짜 아이소메트릭 상자를 만드는 3D Box 도구.
   - 헤드리스 액션으로 쓸 수 있는 불리언.
   - 심볼과 클론.
   - 편집 가능한 한글 텍스트와 PDF/SVG 내보내기.
   - 에이전트용 inkex Python, `--actions`, `--shell`.

   Inkscape 1.5(GTK4, CapyPDF PDF 엔진, Recolor)는 아직 출시되지 않았다. GitLab에 1_5 태그가 없고, 마일스톤 마감일은 2026-04-29였다.
2. **Inkscape 1.4.x 소스(`src/actions/actions-paths.cpp`)는 CLI 액션 13종을 노출한다.** path-union, path-difference, path-intersection, path-exclusion, path-division, path-cut, path-combine, path-break-apart, path-fracture, path-flatten, path-simplify, path-split, path-fill-between-paths다. 덕분에 에이전트가 Shape Builder식 정리를 헤드리스로 할 수 있다. 예를 들어 path-flatten은 겹쳐 쌓인 면의 가려진 부분을 지워 준다. 트레이싱이 만든 색 조각(사용자가 폐기한 이전 작업의 산물)을 깔끔하게 대신할 수 있는 방법이다. 다만 Shape Builder 자체는 GUI에서만 쓸 수 있다.
3. **아이소메트릭 평면 위의 텍스트는 203X 룩에서 빠질 수 없다.**
   - 베이징 상세 크롭(`originals/012-3.jpg`)을 보면 간판(UNIQLO, TAIKOO)이 건물 면에 입혀져 있다. 'TaiKoo Li Sanlitun / 싼리툰 타이구리', '고속철도' 같은 지시선 라벨도 아이소메트릭 축을 따라 놓여 있다.
   - 텍스트를 편집 가능한 상태로 두려면 아핀 스큐가 필요하다. Inkscape, Illustrator, Affinity에는 이 기능이 있다.
   - Penpot에는 스큐가 없다. 플러그인 API에 skew/matrix가 없고, 가이드도 column/row/square뿐이다. 따라서 Penpot에서는 투영된 라이브 라벨을 만들 수 없다.
4. **진짜 아이소메트릭(30°) 평면 행렬을 jdhoek 확장을 실행해 확인했다.**
   - top: `matrix(0.866025 0.5 -0.866025 0.5 tx ty)`
   - left: `matrix(0.866025 0.5 0 1 tx ty)`
   - right: `matrix(0.866025 -0.5 0 1 tx ty)`

   `<text>` 요소에 적용해도 한글은 편집 가능한 상태로 남는다. 스모크 테스트에서 '로마 콘크리트'가 right 평면에서도 `<text>` 요소로 유지되었고, 올바르게 렌더링되었다.
5. **jdhoek 확장의 버그를 찾았다.** jdhoek/inkscape-isometric-projection v4.0(마지막 릴리스 2023-07-14)은 투영 계산은 맞지만, inkex 1.4.1에서는 객체를 제자리에 두지 못한다. `Transform.apply_to_point`의 반환값을 버리기 때문이다(입력 리스트가 바뀌지 않음을 확인했다). 그 결과 객체가 문서 원점을 기준으로 회전하며 튀고, 때로는 캔버스 밖으로 나간다. 투영한 뒤 다시 정렬하거나, 위 세 행렬을 직접 적용해야 한다.
6. **트레이싱 없이 반자동으로 평면 음영을 만들 수 있다.** Inkscape 내장 Render > 3D Polyhedron 확장은 OBJ를 불러와 회전시킨다(y 45°, x 35.264°이면 진짜 아이소메트릭). 이어서 면을 깊이순으로 정렬하고, 각 면을 광원 벡터와 이루는 각도에 따라 음영 처리한다.
   - 결과: 보이는 면마다 깔끔한 `<path>`가 하나씩 생긴다. 12면짜리 OBJ로 선명한 3톤 아이소메트릭 포디움과 타워를 헤드리스로 만들었다.
   - 한계: 한 번 실행할 때 기본색은 하나다. 화가 알고리즘(painter's algorithm)으로 정렬한다. 곡면 메시는 삼각형마다 톤이 하나씩 나온다. 따라서 재질별로 로우폴리 매스를 쓰는 것이 좋다.
7. **macOS에서는 Bash와 CLI가 가장 확실한 에이전트 구동 경로다.**
   - 라이브 모드가 있는 Inkscape MCP 서버는 대부분 D-Bus를 쓴다. Shriinivas/inkmcp는 Linux 전용이다. aravindev/inkscape_mcp는 Ubuntu에서 테스트되었고 Linux/Windows 배지가 붙어 있다.
   - 이 Mac에서 확실한 경로는 Claude Code의 Bash 도구로 Inkscape CLI(`--actions`/`--actions-file`/`--shell`)와 독립 inkex 스크립트를 실행하는 것이다.
   - inkex 1.4.1이 Inkscape 바이너리 없이도 `--id` 선택으로 확장을 헤드리스 실행함을 확인했다. `--no-deps`로 설치했고, 변환에는 PyGObject가 필요 없다.
8. **Penpot 2.18.3(2026-10-06)은 프로젝트로서는 건강하지만, 아이소메트릭 아트에는 맞지 않는다.**
   - 라이선스는 MPL-2.0이고 스타는 61k다.
   - 공식 MCP는 모노레포(`penpot/penpot/mcp`)로 옮겨졌다. 독립 저장소는 2026-02-03에 아카이브되었다. 호스팅 원격 MCP도 있다.
   - MCP는 Penpot 브라우저 탭이 플러그인을 열어 둔 동안에만 작동한다.
   - 불리언, 컴포넌트, 텍스트, PDF/SVG 내보내기는 있다. 그러나 아이소메트릭 그리드도, 스큐도 없고, 플러그인 허브에 아이소메트릭 플러그인도 없다.
   - 아이소메트릭 아트보다는 정보 패널에 알맞다.
9. **Graphite는 필요한 기본 기능을 갖췄지만 아직 알파 단계다.**
   - 라이선스는 Apache-2.0이고 개발이 매우 활발하다.
   - 스냅되는 아이소메트릭 그리드 유형이 이미 있다. 소스에서는 `GridType::Isometric`이며, angle_a/angle_b 기본값은 30/30이다.
   - 불리언 노드, Transform 노드의 스큐, .graphite 파일을 SVG/PNG로 내보내는 graphene-cli도 있다.
   - 그러나 데스크톱 앱은 Discord로 배포되는 릴리스 후보다. PDF 내보내기는 로드맵에만 있고('Basic support for PDF export', Alpha 5), CMYK는 Beta 1 예정이다.
   - A2 인쇄 결과물을 맡기기에는 아직 미성숙하다.
10. **Krita와 Akira도 맞지 않는다.**
    - Krita 6.0.4.1(2026년 9월)에는 아이소메트릭 그리드가 있지만, 문서에 'Isometric doesn't support snapping'이라고 적혀 있다. 벡터 불리언을 쓰면 노드가 많이 늘어난다(KDE bug 400521). 래스터 중심이라 203X용 벡터 도구가 아니다.
    - Akira는 휴면 상태다. 마지막 릴리스는 2021년의 v0.0.16이고, Linux/GTK 전용이다.
11. **이음새(seam) 아티팩트에 대비해야 한다.** 인접한 평면 면을 가장자리끼리 맞대어 그리면, rsvg 렌더에서 면 사이에 얇은 안티앨리어싱 이음새가 보인다(@elchininet/isometric 테스트에서 확인). 각 객체의 실루엣을 가장 어두운 톤으로 밑에 깔거나, 뒷면을 약 0.2 px 겹쳐 그리면 된다. 그러지 않으면 '깔끔한 평면 벡터' 룩에 머리카락 같은 금이 간다. 사용자가 폐기한 이전 작업에서 리뷰어들이 지적한 '밝은 점' 문제와 같은 계열이다.
12. **상용 도구와 비교했다.**
    - **Illustrator**: 네이티브 아이소메트릭 그리드가 없다. 사용자들은 SSR, Shear 도구, 3D & Materials의 아이소메트릭 프리셋에 의존한다. 클래식 3D 프리셋은 35.264° 대신 반올림한 35°를 쓰고, 새 3D 효과를 확장(expand)하면 패스가 지저분해진다. 강점은 Shape Builder, Symbols, Recolor, CJK 조판, CMYK/PDF-X이며, Adobe의 MCP는 Illustrator (Beta)에 있다.
    - **Affinity by Canva**: 이제 무료지만 OSS는 아니다. 가장 가까운 대응물이다. Edit-in-Plane 그리드(Isometric, 2:1, Dimetric, Trimetric, Oblique), 평면 위에 바로 쓰는 텍스트, 스냅, 내장 로컬 MCP 서버(execute_script, render_spread)를 갖췄다.
    - **OSS와의 격차**: '활성 평면 위에 직접 그리기'를 가진 OSS 도구는 없다. Inkscape가 축측 그리드, 투영 행렬, 3D Box 도구를 조합해 가장 가깝게 다가간다.

## 1.3 권장 파이프라인

1. **투영 고정**
   - 203X 베이징 크롭에 맞춰 30° 트루 아이소메트릭으로 정한다.
   - Inkscape 1.4.4는 조사 중에 설치하지 않았다. 사용자가 직접 설치한다(Homebrew cask).
   - A2 세로 문서(420x594 mm)를 만들고, 축측 그리드(Angle X=30, Angle Z=30)와 그리드 교차점 스냅을 켠다.
   - 씬마다 레이어를 하나씩 둔다: 콜로세움과 기초 컷어웨이, Pompeii 유적, Pantheon, 수도교 수로, Portus, 균열 치유 단면, 정보 패널.
2. **히어로 객체는 자동 트레이싱(사용자가 폐기한 이전 작업의 방식) 대신 기하로 만든다.**
   - Blender 로우폴리 매스를 재질별로 OBJ로 내보낸다.
   - Inkscape 내장 3D Polyhedron 확장을 헤드리스로 실행한다. y 45°로 회전한 다음 x 35.264°로 회전하고, 음영을 켜고, centroid z-sort를 쓴다. 그러면 면마다 깔끔한 패스가 하나씩 나온다.
   - 톤을 203X처럼 재질당 약 3톤의 큐레이션 팔레트(top 밝음, left 중간, right 어두움)로 다시 매핑한다.
   - 헤드리스 액션으로 병합·정리한다. 예: `inkscape --actions="select-all;path-flatten;export-filename:out.svg;export-do" in.svg` (또는 path-union / path-fracture).
   - 다른 레인의 Blender→SVG 평면 렌더 결과도 같은 정리 단계에 넣을 수 있다.
3. **평면 위 디테일을 수작업 또는 반자동으로 그린다.**
   - 파사드와 디테일은 평면 상태로 그린다: 콜로세움 아케이드, 수도교 아치와 수로, 판테온 포르티코와 격자천장(coffers), 항구 방파제(moles), 인부 도구.
   - jdhoek 확장이나 정확한 행렬(top 0.866,0.5,-0.866,0.5; left 0.866,0.5,0,1; right 0.866,-0.5,0,1)로 top/left/right 평면에 투영한다. v4.0의 위치 버그 때문에 투영 후 다시 정렬해야 한다.
   - 상자, 블록, 지그재그 공정 플랫폼에는 3D Box 도구를 쓴다(모든 VP 무한대, X 210 / Y 270 / Z 330).
   - 기초 컷어웨이와 3단계 균열 단면에는 Shape Builder / Path ops를 쓴다.
   - 플랫폼 스택이나 단면 블록을 프로그램으로 만들 때는 bun으로 실행한 @elchininet/isometric이 SVG 프리미티브를 내보낼 수 있다.
4. **재사용과 일관성**
   - 인부, 수레, 암포라, 크레인, 석회 가마는 Inkscape 심볼이나 클론으로 한 번만 만든다.
   - 채움은 전역 스와치에 둔다. 그러면 포스터 전체 색을 한꺼번에 바꿀 수 있다.
   - 객체마다 가장 어두운 톤의 실루엣을 밑에 깔아 안티앨리어싱 이음새를 없앤다.
   - 필요하면 약 2 GB인 MightyScape 번들 전체 대신 개별 확장(triangular_grid, import_3d_mesh)만 가져온다.
5. **텍스트**
   - 투영된 라벨과 간판은 같은 행렬을 써서 Inkscape의 편집 가능한 한글 `<text>`로 유지한다. 203X도 지시선 라벨을 아이소메트릭 축을 따라 배치한다.
   - 평면 여백 패널(연표, 비교, 차트)은 Figma(현재 계획) 또는 Scribus에서 만든다.
   - 인쇄용으로는 Inkscape에서 내보낸 아트 PDF를 Scribus 1.6.6에 배치해 CMYK/PDF-X로 출력한다. 단, 테스트에서 Inkscape 1.4의 CMYK PDF 내보내기가 충분히 쓸 만하다고 확인되면 이 단계는 생략할 수 있다.
6. **이 Mac의 에이전트 하네스**
   - Claude가 Bash로 모든 작업을 구동한다. 반복 레시피에는 Inkscape CLI의 `--actions-file`, 긴 세션에는 `--shell`, QA에는 `--query-all`을 쓰고, 여기에 독립 inkex Python 스크립트를 더한다.
   - Inkscape MCP는 선택 사항이다. 라이브 모드는 Linux 중심이다.
   - QA 루프: rsvg-convert로 렌더한 뒤 객체별 고유 채움 수와 전체 패스 수를 센다. 작은 조각(트레이스 노이즈의 징후)을 표시하고, 203X 크롭과 비교한다.

## 1.4 실제로 실행한 검증·시험과 결과

1. **inkex 헤드리스 환경**: 스크래치 `iso-smoke/`에 uv venv(Python 3.12)를 만들었다. `uv pip install --no-deps inkex==1.4.1`과 lxml, numpy, cssselect, tinycss2, pyparsing, packaging, scour, pyserial을 설치했다(PyGObject는 설치하지 않음). venv는 43 MB이고 캐시는 삭제했다.
   - 결과: inkex가 Inkscape 바이너리 없이 헤드리스로 작동한다.
2. **jdhoek v4.0 `axonometric_projection.py` 헤드리스 실행**: `python -I axonometric_projection.py --id=top --conversion=top flat.svg`를 실행하고, 이어서 left와 right도 실행했다.
   - 출력 행렬: top `matrix(0.866025 0.5 -0.866025 0.5 0 0)`, left `matrix(0.866025 0.5 0 1 0 0)`, right `matrix(0.866025 -0.5 0 1 0 0)`.
   - rsvg 렌더에서 평면은 올바르게 나왔지만 객체가 튀었다(right 그룹이 캔버스 밖으로 나감).
   - 원인 확인(inkex 1.4.1): `Transform.apply_to_point`는 새 점을 반환하고 입력 리스트는 그대로 둔다('list after: [200.0, 200.0] returned: -1.46549e-14, 200').
   - 스크래치 `iso-smoke/patched/`의 패치본은 상황을 개선했지만 중앙 정렬을 완전히 되돌리지는 못했다.
   - 한글 '로마 콘크리트' `<text>`는 편집 가능한 상태로 남았고, right 평면에 렌더링되었다(`iso-smoke/work/iso_fixed.png`).
3. **Inkscape 내장 `polyhedron_3d.py` 헤드리스 실행**: gitlab.com/inkscape/extensions master에서 가져온 스크립트를, 생성한 12면 OBJ(포디움+타워)에 `--r1_ax=y --r1_ang=45 --r2_ax=x --r2_ang=35.264 --shade=true --z_sort=cent`로 실행했다.
   - cw_wound=false: 올바른 앞면 6개가 평면 톤 3개(#CCBD9E / #897F6A / #625B4B)로 나왔다. 선명한 트루 아이소메트릭 렌더다(`iso-smoke/work/poly_both.png` 왼쪽 절반).
   - cw_wound=true: 뒷면이 렌더링되었다(와인딩 방향이 틀림).
4. **@elchininet/isometric**: 스크래치 `iso-js/pkg`에 `bun add @elchininet/isometric@4.0.0 jsdom`을 실행했다(37 MB).
   - Bun 1.3.14에서 `esm/index.node.js`를 import하자 'ReferenceError: window is not defined'가 났다. `globalThis.window = undefined`로 해결했다.
   - 트루 아이소메트릭 블록과 SIDE 평면 위의 IsometricText '콜로세움 기초'를 일반 SVG(1446 bytes)로 생성했다.
   - 렌더(`iso-js/out/box.png`)는 정확하지만, 인접한 면 사이에 안티앨리어싱 이음새가 보인다.
5. **gh api / GitLab API 확인**
   - Inkscape 태그: 1.4.4가 2026-05-05, 1.5 태그는 없음.
   - Penpot 릴리스: 2.18.3이 2026-10-06. penpot-mcp는 아카이브되었고 penpot/penpot/mcp로 이전.
   - Graphite 소스: `GridType::Isometric {angle_a, angle_b}`가 있다. graphene-cli는 SVG/PNG 등으로 Export하지만 PDF는 없다.
   - Krita 태그: v6.0.4.1이 2026-09-30.
   - Akira: 마지막 릴리스 v0.0.16(2021).
   - Penpot plugin-types 1.4.2: skew/matrix API가 없고, 가이드는 column/row/square로 제한된다.
   - Inkscape 1.4.x `actions-paths.cpp`: path-union, path-difference, path-intersection, path-exclusion, path-division, path-cut, path-combine, path-break-apart, path-fracture, path-flatten, path-simplify, path-split, path-fill-between-paths가 있다.
6. **실행하지 못한 것**: Inkscape, Penpot, Graphite, Krita, Scribus 바이너리는 설치하지 않았다. 다운로드가 스크래치 한도 50 MB를 넘거나 Docker나 브라우저 세션이 필요했기 때문이다. 따라서 위에 적은 이들 도구의 GUI·CLI 동작은 직접 실행한 결과가 아니라 문서와 소스에 근거한다.

## 1.5 후보 도구 표

적합도 높은 순으로 정렬했다. 적합도가 같으면 원문 순서를 따랐다.

| 이름 | 단계 | 하는 일 | 적합도(1~5) | 라이선스 | 오픈소스 여부 | 유지보수 상태 | 주의사항 | URL |
|---|---|---|---|---|---|---|---|---|
| Inkscape 1.4.4 (core editor + CLI actions + inkex) | vector-authoring | 완전한 OSS SVG 편집기. 스냅되는 축측 그리드(Angle X/Z, 1.4부터 비율 입력). 3D Box 도구는 각 VP를 유한/무한으로 설정할 수 있고, 210/270/330이면 아이소메트릭 상자가 되며 각 면은 별도 svg:path(Box3DSide)다. Shape Builder(1.3+), Path ops, Live Path Effects(Perspective/Envelope, Boolean), Symbols 대화상자, 클론과 타일 클론, 스와치, Pattern editor, Pango/HarfBuzz 기반 CJK 텍스트, Cairo PDF/SVG/PNG 내보내기 | 5 | GPL-2.0-or-later (inkex: GPL-2.0-or-later) | 예 | 안정판 1.4.4 태그 2026-05-05(1.4.3은 2025-12-25). 1.5는 태그 없는 개발 브랜치. GitLab 최근 활동 2026-10-18. Homebrew cask inkscape 1.4.4 | 바이너리로는 스모크 테스트하지 않음(다운로드가 스크래치 한도 50 MB를 크게 넘어 cask 설치는 사용자 판단에 맡김). CMYK/PDF-X: Inkscape CMS 페이지는 1.4부터 CMYK PDF 내보내기가 된다고 하지만 그 페이지에 speculative 표시가 있고, CapyPDF는 미출시 1.5에만 들어감. 인쇄용은 검증하거나 Scribus로 넘길 것. Shape Builder는 GUI 전용. macOS의 GTK3는 패스가 수만 개면 느릴 수 있음. Inkscape 트래커에서 macOS 한글 IME 버그는 찾지 못했지만 캔버스 위 한글 입력은 테스트할 것. 대안은 텍스트 붙여넣기 | https://inkscape.org |
| jdhoek/inkscape-isometric-projection (Axonometric Projections 4.0) | vector-authoring (plane projection) | 평면 2D 아트를 top/left/right 아이소메트릭 평면에 매핑하는 Inkscape 확장. 'Reverse' 옵션으로 되돌릴 수 있음. 다이메트릭(사용자 지정 각도)과 트라이메트릭(두 각도)도 지원. 아핀 변환을 설정하는 방식이라 텍스트와 패스가 편집 가능한 상태로 남음 | 4 | GPL-3.0 | 예 | v4.0 릴리스 2023-07-14, 마지막 push 2023-10-04, 235 stars, 아카이브 안 됨. 열린 이슈 #19 'Generalize to arbitrary axes'. MightyScape 1.2에 포크가 들어 있음 | inkex 1.4.1에서 확인된 버그: 객체 위치가 보존되지 않음(`tr.apply_to_point(center_new)`가 반환값을 버림). 그래서 객체가 튀거나 원점 기준으로 회전함. 한 줄 패치를 해도 두 번째 버그(translate 순서) 때문에 중앙 정렬이 완전히 고쳐지지 않음. 사용 후 재정렬하거나 행렬을 직접 적용할 것. 2023년 이후 커밋이 없어 낡았지만 작고 읽기 쉬움(약 230줄) | https://github.com/jdhoek/inkscape-isometric-projection |
| Adobe Illustrator (contrast only) | vector-authoring (proprietary reference) | 업계 표준 벡터 도구. Shape Builder, Pathfinder, Symbols, Recolor Artwork, Image Trace, 3D & Materials(아이소메트릭 포함 회전 프리셋), Classic 3D, Shear/SSR, Perspective Grid(1, 2, 3점만), CJK composer, CMYK/PDF-X. ExtendScript/UXP 스크립팅. Adobe 도움말(2026-04-16 갱신)에 따르면 Illustrator (Beta)에 MCP 서버가 있음 | 4 | Proprietary subscription | 아니오 | 상용, 활발 | 2026년 버전에 네이티브 아이소메트릭 그리드가 있다는 출처를 찾지 못함. 커뮤니티 스레드에 따르면 클래식 프리셋은 35.264° 대신 35°를 쓰고, 새 3D 효과를 확장하면 패스가 지저분해짐. Adobe 도움말 페이지는 열지 못함(HTTP 403) | https://helpx.adobe.com/illustrator/using/create-3d-graphics.html |
| Affinity by Canva (contrast only; free, not OSS) | vector-authoring (proprietary reference) | 축측 그리드 모드(Isometric, 2:1 Isometric, Dimetric, Oblique, Trimetric L/R)와 Enable Planes(Front/Side/Top). 도형과 아티스틱 텍스트를 활성 평면 위에서 바로 그리고 변형함. Fit In Plane으로 기존 아트를 변환하고, 노드가 그리드 선과 교차점에 스냅됨. 내장 로컬 MCP 서버(execute_script, render_spread) | 4 | Proprietary (Canva의 2025년 재출시 이후 무료, AI 기능은 유료) | 아니오 | 상용, 활발(Affinity 3.2.x 빌드) | 기능 인용은 iPad용 Designer 2 도움말 페이지에서 가져옴. macOS용 'Affinity by Canva' MCP 세부 내용은 Canva 문서가 아니라 디렉터리 목록에서 확인한 것 | https://affinity.help/designer2ipad/en-US.lproj/pages/DesignAids/grids_axonometric.html |
| Inkscape built-in Render > 3D Polyhedron (polyhedron_3d) | flat-render (OBJ to flat-shaded vector faces) | Wavefront OBJ를 불러와('Load from file') 최대 6번의 축 회전과 스케일을 적용하고, 뒷면을 제거(cull)하고, z 기준(min/max/centroid)으로 정렬한 뒤 각 면을 polygon 패스로 그림. 광원 벡터와 이루는 각도에 따라 면을 어둡게 해, 래스터 단계 없이 면마다 평면 톤을 줌 | 3 | GPL-2.0-or-later (inkscape/extensions에 포함) | 예 | 코어 extensions 저장소의 일부. GitLab 활동 2026-10-13 | 한 번 실행할 때 기본색 하나. 서로 관통하거나 오목한 메시에서는 화가 알고리즘 정렬이 실패함. 음영 비율이 고정(angle/π로 어둡게)이라 큐레이션한 3톤 팔레트로 다시 매핑해야 함. namedview 중심이 없어 헤드리스 출력은 (0,0)에 놓이므로 나중에 이동해야 함. cw_wound를 OBJ 와인딩에 맞춰야 함(CCW 면에는 false가 작동) | https://gitlab.com/inkscape/extensions/-/blob/master/polyhedron_3d.py |
| @elchininet/isometric (JS/TS SVG isometric library) | vector-authoring (programmatic) / assets | TOP/FRONT/SIDE 평면 위에 SVG 아이소메트릭 프리미티브(IsometricRectangle, Circle, Path, StarPolygon, Group)와 IsometricText(평면 위 텍스트)를 생성. `getSVGCode()`가 일반 SVG를 반환. Node/Deno 빌드는 jsdom 사용 | 3 | Apache-2.0 | 예 | npm 4.0.0 게시 2026-03-29, 마지막 push 2026-10-11, 242 stars | Bun에서 node 빌드를 import하면 'ReferenceError: window is not defined'가 남. import 전에 `globalThis.window = undefined`를 설정하면 해결. 인접 면에 안티앨리어싱 이음새가 보이므로 밑깔개(underlay)를 추가할 것. 프리미티브만 제공하므로 복잡한 형태는 IsometricPath로 직접 작성해야 함 | https://github.com/elchininet/isometric |
| Scribus 1.6.6 (final A2 layout and typography handoff) | layout / typography / print | OSS 전자출판(DTP). 프레임, 스타일, CMYK 색 관리, PDF/X 내보내기, Python 스크립터. 벡터 아트(PDF/SVG)를 배치하고 빽빽한 한글 정보 패널을 담음 | 3 | GPL-2.0-or-later (GitHub 미러는 NOASSERTION 표시) | 예 | 안정판 1.6.6(2026년 4월, Wikipedia/FileHorse 기준), 개발판 1.7.3. GitHub 미러 push 2026-10-15 | 릴리스 날짜와 버전은 scribus.net이 아니라 Wikipedia와 다운로드 미러에서 확인함. SVG 가져오기 충실도가 완벽하지 않으므로 Inkscape에서 내보낸 PDF를 배치하는 편이 안전함. 일반적인 사용에서는 라이브 텍스트 프레임에 스큐를 줄 수 없으므로 투영된 라벨은 아트 레이어에 둘 것. 스모크 테스트하지 않음 | https://www.scribus.net |
| aravindev/inkscape_mcp | mcp | 포트만토(portmanteau) 도구 8개(file, vector, analysis, system, extension, gradient, metadata, live)를 가진 FastMCP 서버. `--actions`/`--export`로 Inkscape를 헤드리스 실행하거나, D-Bus로 GUI 창과 나란히 라이브 실행 | 3 | MIT | 예 | 생성 2026-05-23, 마지막 push 2026-10-05, 78 stars, PyPI에 inkscape-mcp로 게시 | 플랫폼 배지가 Linux \| Windows이고 설정 안내는 Ubuntu 기준. 라이브 모드는 D-Bus를 쓰므로 macOS에서는 헤드리스 경로만 작동할 것으로 예상(미확인). 이 Mac에서는 Bash와 Inkscape CLI로 새 의존성 없이 같은 헤드리스 범위를 다룰 수 있음 | https://github.com/aravindev/inkscape_mcp |
| 0xDarkMatter/claude-mods 'isometric-ops' agent skill | agent-skill | 투영 결정(30° 트루 아이소메트릭 vs 2:1 다이메트릭), 기계 검증된 상수(cos30 = 86.602% SSR 압축, RotX 54.736° / RotZ 45° 카메라), SVG/CSS/three.js 경로, Blender 사전 렌더 경로를 다루는 Claude 스킬. iso-math.py 스크립트(그리드 SVG, Illustrator/Figma/SVG용 변환 레시피)와 미리 생성된 트루 아이소메트릭/다이메트릭 그리드 SVG 포함 | 3 | MIT | 예 | 저장소 push 2026-10-14, 66 stars | 인쇄 포스터보다는 웹·게임 에셋을 겨냥함. 연결된 'iso-studio' 저장소(github.com/0xDarkMatter/iso-studio)는 404를 반환함. SKILL.md만 읽었고 참조 파일은 모두 읽지 않음 | https://github.com/0xDarkMatter/claude-mods/tree/main/skills/isometric-ops |
| Penpot 2.18.3 + official Penpot MCP | vector-authoring / layout / mcp | 웹 기반 OSS 디자인 도구. 불리언(union, difference, exclude, intersection), 컴포넌트와 배리언트, 타이포그래피, 디자인 토큰, PNG/JPEG/SVG/PDF 내보내기. 플러그인 API에 createPath, createBoolean, createShapeFromSvg, createText, createComponent, flatten이 있음. 공식 MCP(로컬 `npx @penpot/mcp@stable` 또는 호스팅 원격)가 에이전트가 작성한 코드를 Plugin API에 대해 실행 | 2 | MPL-2.0 | 예 | 2.18.3 릴리스 2026-10-06, 저장소 push 2026-10-17, 61.3k stars. penpot/penpot-mcp 저장소는 2026-02-03에 아카이브되어 penpot/penpot/mcp로 이전. npm @penpot/mcp stable은 2.15.4(2026-06-02), next는 2.17.0 | 내보내기 문서에 따르면 모든 SVG 기능에 대해 PDF 충실도가 보장되지 않음. CMYK 없음. 브라우저 탭이 절전되면 MCP가 멈춤. 플러그인 허브의 'Dimensio'와 'Planeshifter - 3D Transformations' 항목은 확인하지 못함 | https://github.com/penpot/penpot |
| Graphite (graphite.art) | vector-authoring (procedural node graph) | Rust/WebGPU 기반 노드형 절차적 벡터 편집기. 스냅되는 아이소메트릭 그리드 유형(angle_a/angle_b, 기본 30/30), 불리언 연산 노드, 스큐가 있는 Transform 노드, 텍스트 도구, .graphite 문서를 SVG/PNG/JPG/WebP/TIFF/GIF로 내보내는 graphene-cli 'export' | 2 | Apache-2.0 (저장소에 LICENSE-MIT도 있음) | 예 | 저장소 push 2026-10-17, 27.6k stars. 홈페이지에 따르면 데스크톱 앱은 릴리스 후보 단계(Discord로 링크 제공). 로드맵에 'Basic support for PDF export'는 Alpha 5, CMYK는 Beta 1 | 한국어/CJK 텍스트 렌더링 미확인. 심볼/인스턴스 라이브러리는 문서화된 기능이 아님. 릴리스 후보 데스크톱 빌드는 GitHub 릴리스에 없음(유일한 릴리스 항목은 2022년의 'latest-stable'). 남은 디스크 9 GiB로는 소스 빌드가 버거움 | https://github.com/GraphiteEditor/Graphite |
| MightyScape 1.2 (FabLab Chemnitz extension collection) | vector-authoring (extensions) | 유지보수되는 대규모 Inkscape 확장 묶음. 관련 확장: isometric_projection(jdhoek 포크), import_3d_mesh, perspective_grid, another_perspective, clones_in_perspective, triangular_grid, offset_paths, label_guides | 2 | GPL-3.0 | 예 | README에 Inkscape 1.4.4(2026-05-05)로 테스트했다고 적혀 있음. push 2026-08-22, 83 stars | README에 따르면 전체 설치가 약 2 GB이므로 개별 확장 폴더만 복사할 것. 설명에는 Windows와 Linux라고 되어 있지만 README에는 macOS용 .dmg Inkscape도 나옴. import_3d_mesh는 테스트하지 않음 | https://github.com/eridur-de/mightyscape-1.2 |
| Inkscape built-in Render > Grids > Isometric Grid | assets (grid) | 아이소메트릭 그리드를 실제 패스 객체로 그림. major, minor, sub-minor 분할과 두께 지정 | 2 | GPL-2.0-or-later | 예 | 코어 extensions 저장소, 2026-10 활동 | 스냅 그리드가 아니라 객체를 만들므로 내보내기 전에 삭제하거나 잠글 것 | https://gitlab.com/inkscape/extensions/-/blob/master/grid_isometric.inx |
| jnweiger/inkscape-flat-projection | vector-authoring (extrusion) | Extensions > Modify Path > Flat Projection. 2D 패스에 3D 회전을 적용하고 평행(축측) 투영으로 다시 2D로 돌리면서 옆벽을 생성(Knuth의 algorithm T) | 2 | GPL-2.0 | 예 | 마지막 push 2023-11-01, 4 stars | README에 깊이나 음영 파라미터, Inkscape 버전 호환성이 문서화되어 있지 않음. 테스트하지 않음 | https://github.com/jnweiger/inkscape-flat-projection |
| HKUDS/CLI-Anything: cli-anything-inkscape skill | agent-skill / harness | SVG 편집용으로 JSON을 출력하는 상태 유지형 CLI와 REPL(JSON 프로젝트 상태, document/shape 명령)에 SKILL.md가 딸림. GIMP·Blender 하네스와 같은 패턴으로 만듦 | 2 | Apache-2.0 | 예 | 저장소 push 2026-09-22, 54.1k stars | 불리언이나 투영을 어디까지 다루는지 확인하지 않음. Inkscape 설치가 필요함 | https://github.com/HKUDS/CLI-Anything/tree/main/skills/cli-anything-inkscape |
| sandraschi/inkscape-mcp | mcp | 헤드리스 우선 Inkscape MCP. 60개 이상의 연산(생성, 불리언, envelope 같은 LPE, 텍스트, PNG/PDF/EPS/DXF 내보내기)과 대시보드 웹앱 제공 | 2 | MIT | 예 | push 2026-10-12, 88 stars | 설치 문서가 Windows 중심(start.bat, winget). macOS에서 테스트하지 않음. 단순 CLI 호출 위에 의존성 계층이 하나 더 생김 | https://github.com/sandraschi/inkscape-mcp |
| Shriinivas/inkmcp | mcp | 실행 중인 Inkscape를 D-Bus로 라이브 제어. 요소 생성, 임의 inkex 코드 실행, 뷰포트 스크린샷 | 1 | AGPL-3.0 | 예 | 마지막 push 2026-01-14, 74 stars | 이 macOS 환경에서는 실행되지 않음 | https://github.com/Shriinivas/inkmcp |
| Krita 6.0.4.1 (vector layers) | vector-authoring (secondary) | SVG 기반 벡터 레이어를 가진 페인팅 앱. 5.3/6.0의 새 텍스트 엔진(캔버스 위 OpenType 텍스트, 도형 안·패스 위 텍스트), 벡터용 칼(knife) 도구, 아이소메트릭 그리드 도커, Python 스크립팅 | 1 | GPL-3.0 | 예 | v6.0.4.1 태그 2026-09-30, 매우 활발 | 벡터 레이어의 SVG 내보내기나 PDF 내보내기는 확인하지 않음 | https://invent.kde.org/graphics/krita |
| Akira | vector-authoring | 네이티브 Linux(Vala/GTK) UI/UX 디자인 앱 | 1 | GPL-3.0 | 예 | 마지막 릴리스 v0.0.16(2021-08-15). 2023년 공백 후 2025년 12월 말에 커밋 2개뿐 | macOS에서는 쓸 수 없음 | https://github.com/akiraux/Akira |
| PixiEditor 2.1 | vector-authoring (secondary) | 노드 그래프와 벡터 도형(Bool Operation 노드 포함)을 가진 '범용 2D 편집기' | 1 | LGPL-3.0 | 예 | 2.1.2.4 릴리스 2026-09-04, push 2026-10-16, 8.1k stars | 저장소 메타데이터와 불리언 노드 문서 페이지만 확인함 | https://github.com/PixiEditor/PixiEditor |
| SVG-Edit | vector-authoring | 브라우저 기반 SVG 편집기 | 1 | MIT | 예 | 마지막 릴리스 v7.3.3(2023-12-10), 저장소 push 2026-08-05, 7.9k stars | 메타데이터 외에는 평가하지 않음 | https://github.com/SVG-Edit/svgedit |
| LibreOffice Draw (3D extrusion) | vector-authoring (niche) | 사용자 정의 도형을 조명·표면 설정과 함께 3D로 압출. API의 ProjectionMode가 평행 투영과 원근 투영을 지원. SVG/PDF 내보내기, UNO/Python과 헤드리스 soffice로 스크립팅 가능 | 1 | MPL-2.0 | 예 | 활발히 릴리스 중(세부 재확인은 안 함) | 테스트하지 않음. 3D를 SVG로 내보낼 때의 벡터 충실도 미확인 | https://books.libreoffice.org/en/DG75/DG7507-3DObjects.html |
| isomer / obelisk.js / isoflow (isometric JS libs and diagram tool) | assets / generation | isomer: HTML5 canvas에 그리는 아이소메트릭 도형. obelisk.js: canvas 위 픽셀아트 아이소메트릭. isoflow(markmanx/isoflow): 아이콘 팩을 갖춘 아이소메트릭 네트워크 다이어그램 편집기 | 1 | isomer MIT, isoflow MIT, obelisk.js는 GitHub에서 NOASSERTION | 예 | isomer 마지막 push 2022-04-20(2.9k stars), obelisk.js 2019-06-29, isoflow 2025-09-17(1.7k stars) | 완전성을 위해 목록에 넣었고 테스트하지 않음 | https://github.com/jdan/isomer |

### 1.5.1 후보별 보충 정보 (적합도 근거, 에이전트 구동, 로컬 설치, 근거 URL)

적합도 근거의 (a)~(f)는 원문이 쓴 여섯 요구사항이다: (a) 아이소메트릭 그리드·스냅, (b) 평면 위 그리기·투영, (c) 불리언, (d) 심볼·클론 재사용, (e) 편집 가능한 한글 텍스트와 PDF/SVG 내보내기, (f) 에이전트 구동.

**Inkscape 1.4.4**
- 적합도 근거:
  - (a) 충족: 축측 그리드와 스냅이 있다.
  - (b) 부분 충족: '평면 위에 그리기' 모드는 없지만 투영 행렬, jdhoek 확장, Perspective LPE로 대신할 수 있다.
  - (c) 충족: Shape Builder가 있고, path 액션 13종을 헤드리스로 쓸 수 있다.
  - (d) 충족: 심볼과 클론이 있다.
  - (e) 충족: 스큐 행렬을 적용해도 한글 `<text>`가 편집 가능하고, PDF/SVG로 내보낼 수 있다.
  - (f) 충족: `--actions`, `--actions-file`, `--shell`, `--query-all`, inkex Python 확장이 있다.
  - 히어로 객체에서는 VTracer 단계(사용자가 폐기한 이전 작업)를 깔끔한 기하로 대체할 수 있다.
- 에이전트 구동: CLI(`inkscape --actions` / `--actions-file` / `--shell` / `--export-type=pdf`), 헤드리스로 실행할 수 있는 Python inkex 확장, 여러 커뮤니티 MCP.
- 로컬 설치: 아니오. Inkscape는 설치하지 않았다. inkex 1.4.1만 테스트용 스크래치 venv에 설치했다.
- 근거 URL: https://gitlab.com/inkscape/inkscape/-/tags · https://wiki.inkscape.org/wiki/Release_notes/1.4 · https://wiki.inkscape.org/wiki/Release_notes/1.3 · https://wiki.inkscape.org/wiki/Release_notes/1.5 · https://inkscape-ltlnx.readthedocs.io/en/latest/pos-transform/positioning/grids.html · https://wiki.inkscape.org/wiki/Using_the_Command_Line · https://gitlab.com/inkscape/inkscape/-/blob/1.4.x/src/actions/actions-paths.cpp · https://gitlab.com/inkscape/inkscape/-/blob/master/src/object/box3d-side.cpp · https://archive.flossmanuals.net/inkscape/ch011_3d-box-tool.html · https://pypi.org/project/inkex/

**jdhoek/inkscape-isometric-projection**
- 적합도 근거: 203X의 수법과 정확히 같다. 파사드, 간판, 라벨(콜로세움 아케이드, 수도교 아치, 판테온 포르티코 명문, 한글 라벨)을 평면 상태로 그린 뒤, 편집 가능한 채로 평면에 투영한다. 스모크 테스트에서 올바른 행렬과, right 평면 위에서도 편집 가능한 한글 `<text>`를 확인했다.
- 에이전트 구동: 예. inkex를 설치한 뒤 `python axonometric_projection.py --id=<id> --conversion=top|left|right [--reverse=true] in.svg > out.svg`로 헤드리스 실행한다.
- 로컬 설치: 스크래치에 다운로드만 했다.
- 근거 URL: https://github.com/jdhoek/inkscape-isometric-projection · https://github.com/jdhoek/inkscape-isometric-projection/releases · https://inkscape.org/~jdhoek/%E2%98%85inkscape-axonometric-projections-40

**Adobe Illustrator (contrast only)**
- 적합도 근거: 203X류 스튜디오가 흔히 쓰는 도구다. Inkscape와의 격차는 아이소메트릭 기능이 아니라 주로 완성도 쪽이다(Shape Builder UX, Recolor, CJK 조판, CMYK/PDF-X). Illustrator에도 네이티브 아이소메트릭 그리드는 없다.
- 에이전트 구동: ExtendScript/UXP, Illustrator (Beta)의 공식 MCP, ie3jp/illustrator-mcp-server(MIT, 168 stars) 같은 커뮤니티 MCP.
- 로컬 설치: 아니오.
- 근거 URL: https://community.adobe.com/t5/illustrator-discussions/isometric-mode-not-really-isometric/m-p/13433682/highlight/true · https://community.adobe.com/t5/illustrator/3d-rotate-isomatric-doesn-work-properly/td-p/8731093?page=1 · https://helpx.adobe.com/illustrator/desktop/connect-with-other-apps-and-tools/connect-illustrator-to-ai-tools.html · https://github.com/ie3jp/illustrator-mcp-server

**Affinity by Canva (contrast only)**
- 적합도 근거: 검토한 도구 가운데 아이소메트릭 드로잉 UX가 가장 좋고, 무료다. 동시에 OSS의 주요 격차를 보여 준다. Inkscape에는 '활성 평면 위에 그리기' 모드가 없어서, 평면 투영을 별도 단계로 해야 한다.
- 에이전트 구동: 내장 로컬 MCP(Claude 커넥터 목록 기준), andre-carbajal/affinity-mcp-bridge 같은 커뮤니티 브리지.
- 로컬 설치: 아니오.
- 근거 URL: https://affinity.help/designer2ipad/en-US.lproj/pages/DesignAids/grids_axonometric.html · https://www.canva.com/es_mx/help/free-affinity-access/ · https://claude.com/connectors/affinity-106b90 · https://github.com/andre-carbajal/affinity-mcp-bridge

**Inkscape built-in Render > 3D Polyhedron**
- 적합도 근거: 기존 Blender 모델에서 203X식 면 분할 벡터로 가는, 트레이싱 없는 다리다. y=45°로 회전한 다음 x=35.264°로 회전하면 트루 아이소메트릭이 된다. 스모크 테스트에서 포디움과 타워가 3톤짜리 선명한 패스 6개로 나왔다. 재질 단위로 작동하므로, 재질별 로우폴리 매스를 내보내고 결과를 path-flatten이나 path-union으로 합친다.
- 에이전트 구동: 예. inkex로 헤드리스 실행한다: `python polyhedron_3d.py --obj=from_file --spec_file=/abs/model.obj --r1_ax=y --r1_ang=45 --r2_ax=x --r2_ang=35.264 --show=fce --shade=true --z_sort=cent blank.svg`
- 로컬 설치: 스크립트를 스크래치에 내려받아 스크래치 inkex venv로 실행했다.
- 근거 URL: https://gitlab.com/inkscape/extensions/-/blob/master/polyhedron_3d.inx · https://gitlab.com/inkscape/extensions/-/blob/master/polyhedron_3d.py

**@elchininet/isometric**
- 적합도 근거: 에이전트가 생성하는 선명한 구조 요소에 좋다. 신문 제작 포스터식 지그재그 공정 플랫폼, 균열 치유 단면 블록, 항구 부두, 평면 위 한글 텍스트에 쓸 수 있다. 스모크 테스트에서 정확한 트루 아이소메트릭 면과, side 평면 위에서 편집 가능한 '콜로세움 기초' `<text>`를 만들었다.
- 에이전트 구동: 예. bun으로 스크립팅한다(jsdom 필요). 출력 SVG는 Inkscape와 Figma로 가져올 수 있다.
- 로컬 설치: 스크래치에만 설치했다(`bun add @elchininet/isometric@4.0.0 jsdom`, 37 MB).
- 근거 URL: https://github.com/elchininet/isometric · https://www.npmjs.com/package/@elchininet/isometric

**Scribus 1.6.6**
- 적합도 근거: 203X의 나머지 절반인 '빽빽하지만 질서 있는 타이포그래피 정보 디자인'을 맡는다. Inkscape의 CMYK 지원이 불확실한 상황에서 인쇄에 맞는 출력(CMYK, PDF/X)도 해 준다. 아이소메트릭 아트 자체는 여전히 Inkscape에서 만든다.
- 에이전트 구동: Python 스크립터(GUI 안에서 실행). 헤드리스 사용은 제한적이다.
- 로컬 설치: 아니오.
- 근거 URL: https://en.wikipedia.org/wiki/Scribus · https://github.com/scribusproject/scribus · https://inkscape.org/learn/cms

**aravindev/inkscape_mcp**
- 적합도 근거: 가장 완성도 높은 Inkscape MCP이며, Inkscape 1.4.4에 대해 테스트되었다. 헤드리스 연산(불리언, 내보내기, 확장)이 이 프로젝트에 필요한 작업과 맞는다.
- 에이전트 구동: MCP(`uvx inkscape_mcp`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/aravindev/inkscape_mcp · https://pypi.org/project/inkscape-mcp/

**0xDarkMatter/claude-mods 'isometric-ops'**
- 적합도 근거: 에이전트에게 일관된 투영 계산과 그리드 에셋을 준다. 그래서 모든 씬(Colosseum, Pompeii, Pantheon, aqueduct, Portus)이 같은 축을 공유하게 되는데, 이것이 203X의 핵심 특징이다. cos30 스케일 없이 스큐만 거는 흔한 실수도 짚어 준다.
- 에이전트 구동: 스킬(SKILL.md + scripts).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/0xDarkMatter/claude-mods/blob/main/skills/isometric-ops/SKILL.md

**Penpot 2.18.3 + official Penpot MCP**
- 적합도 근거: (c), (d), (e), (f)는 강하다. 하지만 (a)와 (b)가 없다. 가이드는 column/row/square뿐이고, 플러그인 API에 skew/matrix가 없으며, 플러그인 허브에 아이소메트릭 플러그인도 없다. 따라서 투영된 아트와 투영된 라벨은 다른 곳에서 미리 만들어 와야 한다. Figma 대안으로 여백 정보 패널을 담을 수는 있다.
- 에이전트 구동: 공식 MCP(execute_code, high_level_overview, penpot_api_info, export_shape, import_image). MCP 플러그인이 열린 Penpot 탭이 계속 떠 있어야 한다.
- 로컬 설치: 아니오. plugin-types tarball만 스크래치에서 살펴보았다.
- 근거 URL: https://github.com/penpot/penpot/releases/tag/2.18.0 · https://github.com/penpot/penpot/tree/develop/mcp · https://github.com/penpot/penpot-mcp · https://help.penpot.app/mcp/ · https://penpot.app/penpothub/plugins · https://help.penpot.app/user-guide/export-import/exporting-layers/ · https://www.npmjs.com/package/@penpot/plugin-types

**Graphite**
- 적합도 근거: 서류상으로는 필요한 기본 요소를 갖췄다. 아이소메트릭 스냅 그리드, 아케이드와 격자천장을 위한 절차적 반복, 불리언이 있다. 하지만 알파 단계이고 PDF 내보내기가 없어서, 지금 A2 인쇄 마스터를 맡기기에는 믿기 어렵다.
- 에이전트 구동: graphene-cli(Rust 소스에서 빌드). 서드파티 graphite-editor-mcp가 있으나 0 stars.
- 로컬 설치: 아니오.
- 근거 URL: https://graphite.art/ · https://graphite.art/features/ · https://github.com/GraphiteEditor/Graphite/blob/master/editor/src/messages/portfolio/document/utility_types/misc.rs · https://github.com/GraphiteEditor/Graphite/blob/master/node-graph/graphene-cli/src/main.rs

**MightyScape 1.2**
- 적합도 근거: Inkscape 1.4.4에서 작동하는 것으로 알려진 확장(예: import_3d_mesh, triangular_grid)을 하나씩 골라 오는 공급원으로 유용하다.
- 에이전트 구동: 다른 inkex 확장과 같다(헤드리스 Python).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/eridur-de/mightyscape-1.2 · https://github.com/eridur-de/mightyscape-1.2/tree/master/extensions/fablabchemnitz

**Inkscape built-in Isometric Grid**
- 적합도 근거: 인쇄 가능한 가이드 레이어나 밑깔개로 쓰기 좋고, 패스 노드를 스냅 대상으로 쓸 수도 있다. 라이브 스냅에는 네이티브 축측 그리드가 더 낫다.
- 에이전트 구동: 헤드리스 inkex.
- 로컬 설치: 아니오.
- 근거 URL: https://gitlab.com/inkscape/extensions/-/blob/master/grid_isometric.inx

**jnweiger/inkscape-flat-projection**
- 적합도 근거: Inkscape 밖으로 나가지 않고 평면도(경기장 타원, 항구 방파제, 기초 평면)를 옆벽이 있는 아이소메트릭 각기둥으로 압출할 수 있다.
- 에이전트 구동: 헤드리스 inkex(추정).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/jnweiger/inkscape-flat-projection

**HKUDS/CLI-Anything: cli-anything-inkscape**
- 적합도 근거: SVG 편집 위에 얹는 에이전트 친화적 JSON 계층이다. 다만 이 프로젝트에 필요한 것은 Inkscape 자체 CLI와 inkex로 이미 해결된다.
- 에이전트 구동: CLI + 스킬(`pip install cli-anything-inkscape`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/HKUDS/CLI-Anything/blob/main/skills/cli-anything-inkscape/SKILL.md

**sandraschi/inkscape-mcp**
- 적합도 근거: 기능 범위(불리언, LPE envelope, PDF 내보내기)가 요구사항과 맞는다.
- 에이전트 구동: MCP(stdio/HTTP), .mcpb 번들.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/sandraschi/inkscape-mcp

**Shriinivas/inkmcp**
- 적합도 근거: 실시간 공동 편집이 가능하다면 이상적이겠지만, README에 'Currently Linux Only'(D-Bus)라고 명시되어 있다.
- 에이전트 구동: MCP.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/Shriinivas/inkmcp

**Krita 6.0.4.1**
- 적합도 근거: 래스터 중심이다. 문서에 'Isometric doesn't support snapping'이라고 되어 있고, 벡터 불리언을 쓰면 노드가 많이 늘어난다(KDE bug 400521). 깔끔한 203X 벡터 마스터로 가는 경로가 아니다.
- 에이전트 구동: Python 스크립팅 API, 커뮤니티 krita-mcp 서버(예: nanayax3/krita-mcp, 48 stars).
- 로컬 설치: 아니오.
- 근거 URL: https://docs.krita.org/en/reference_manual/dockers/grids_and_guides.html · https://docs.krita.org/en/reference_manual/layers_and_masks/vector_layers.html · https://linuxiac.com/krita-5-3-and-6-0-released-with-new-text-engine-and-wayland-hdr-support/ · https://bugs.kde.org/show_bug.cgi?id=400521

**Akira**
- 적합도 근거: 휴면 상태이고 Linux 전용이다. 아이소메트릭 기능이 없다.
- 에이전트 구동: 아니오.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/akiraux/Akira · https://github.com/akiraux/Akira/releases

**PixiEditor 2.1**
- 적합도 근거: 픽셀아트와 일반 2D에 초점을 둔다. 아이소메트릭 그리드나 인쇄용 PDF 워크플로를 찾지 못했다.
- 에이전트 구동: 미확인.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/PixiEditor/PixiEditor · https://pixieditor.net/docs/usage/node-graph/nodes/shapes/bool-operation/

**SVG-Edit**
- 적합도 근거: 아이소메트릭 그리드, 투영, 심볼 워크플로, 인쇄용 PDF가 없다. A2 포스터에 쓰기에는 너무 기초적이다.
- 에이전트 구동: JS(브라우저 안).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/SVG-Edit/svgedit

**LibreOffice Draw (3D extrusion)**
- 적합도 근거: 평행 투영으로 음영이 들어간 입체를 만들 수는 있다. 하지만 쓸 수 있는 도형 종류가 제한적이고 톤을 제어하기 어렵다. 203X 제작 경로로는 맞지 않는다.
- 에이전트 구동: UNO Python API, 헤드리스 soffice.
- 로컬 설치: 아니오.
- 근거 URL: https://books.libreoffice.org/en/DG75/DG7507-3DObjects.html · https://api.libreoffice.org/docs/idl/ref/ProjectionMode_8idl.html

**isomer / obelisk.js / isoflow**
- 적합도 근거: 출력이 canvas나 픽셀이거나, 다이어그램 아이콘 스타일이다. 인쇄 품질의 편집 가능한 벡터 아트를 내는 것은 없다. SVG 용도로는 @elchininet/isometric이 이들을 대체한다.
- 에이전트 구동: JS 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/jdan/isomer · https://github.com/nosir/obelisk.js · https://github.com/markmanx/isoflow

---

# 2부. C 레인: 코드 기반 아이소메트릭·의사 3D SVG 생성

조사 범위: AI 코딩 에이전트가 직접 작성하는 코드로 아이소메트릭·의사 3D SVG를 생성하는 방법(순수 벡터 출력, 트레이싱 없음).

## 2.1 한눈에 보는 결론

- 코드 기반 벡터 출력으로 바꾸면 면마다 닫힌 패스 하나에 단색 채움 하나가 된다. 그래서 리뷰어들이 반복해서 지적한 트레이스 노이즈(사용자가 폐기한 이전 작업의 색 조각·밝은 점)가 원천적으로 생기지 않는다. 다만 203X 수준의 디테일은 어떤 라이브러리도 대신 만들어 주지 않으므로, 부품 단위로 직접 작성해야 한다.
- 가장 유력한 후보는 wheresryan22/anatomy(Agent Skill + 무의존 키트, MIT)다. 아이소메트릭 카메라, 4톤 음영, 회전체(돔·드럼), 깊이 순서 감사, 헤드리스 Chrome QA를 갖췄다. 단, CSS var() 톤을 fill 속성으로 굽는(bake) 단계가 꼭 필요하다.
- 보조 도구: Paper.js(아치 개구부, 컷어웨이, 같은 톤 병합용 불리언), @elchininet/isometric(진짜 타원 호), three.js SVGRenderer + three-bvh-csg(복잡한 콜로세움과 컷어웨이), Shapely(이미 설치됨).
- 정보 디자인 쪽은 Typst+CeTZ 또는 D3를 쓴다. 성능은 제약이 아니며, 실제 한계는 Figma 레이어 수다.

## 2.2 핵심 발견

1. **코드 기반 벡터 출력은 리뷰어들이 계속 지적해 온 문제를 해결한다.** 이 문제는 사용자가 폐기한 이전 트레이싱 작업에서 나온 것이다. 코드로 그리면 모든 면이 단색 채움 하나를 가진 닫힌 패스 하나가 되므로, 트레이스 노이즈(색 조각, 규칙적인 밝은 점)가 생길 수 없다. 다만 어떤 라이브러리도 203X 수준의 디테일을 스스로 더해 주지는 않는다. 디테일은 부품 단위로 직접 써야 한다(부품 목록, 랜드마크별로 정한 스케일, 고정된 카메라 하나).
2. **이 레인에서 가장 강력한 발견은 wheresryan22/anatomy다.** Agent Skill과 무의존 키트로 이루어졌다(MIT, v1.1.0 2026-10-12, 15.2k stars). 제공하는 기능은 다음과 같다.
   - 아이소메트릭 카메라. 기본 elevation 30°, azimuth 45°로, 203X 포스터가 쓰는 2:1 다이메트릭 각도가 된다.
   - 음영 톤 4단계(bucketed)를 가진 압출 솔리드.
   - 임의 축 기준 회전체(돔, 드럼, 종)와 sphereOf.
   - 곡면 위의 호와 리브 선.
   - 기하·깊이 순서 감사.
   - 헤드리스 Chrome 캡처와 선 끝(line-end) QA 스크립트.

   README에는 사람이나 정확한 지도가 아니라 기계를 그리는 도구라고 적혀 있다. 톤은 단색 CSS var() 테마다.
3. **확인된 함정: anatomy가 내는 SVG는 반드시 구워야 한다.**
   - anatomy의 standalone SVG는 톤을 CSS 커스텀 속성에 둔다. rsvg-convert 2.62.2는 모든 것을 단색 검정으로 그렸다.
   - 각 클래스를 명시적 fill/stroke 속성으로 바꾸는 작은 bake 단계를 거치자 올바르게 렌더링되었다. 돔이 깔끔한 포스터화 밴드로 나와, 203X의 밴드 진 곡면과 매우 비슷했다.
   - 인쇄나 Figma로 보낼 SVG는 먼저 일반 fill 속성으로 구워야 한다(var() 없음, `<style>` 없음).
   - Figma가 var()를 어떻게 처리하는지는 테스트하지 않았다.
4. **@elchininet/isometric은 API가 가장 작고, 진짜 타원 호를 낸다.**
   - `IsometricPath.curveTo`가 진짜 SVG 타원 호를 출력한다(확인: `A 73.484684 42.426392 -119.999977 ...`). 콜로세움 아치에 알맞다.
   - 하지만 조명도, 깊이 정렬도 없다. 그리는 순서가 곧 추가한 순서다.
   - v4.0.0 Node 엔트리는 dynamic import 전에 `globalThis.window = undefined`를 설정하지 않으면 Bun 1.3.14와 Node 26.7 모두에서 크래시한다('window is not defined').
5. **Zdog는 조명이 없어서 돔 음영을 흉내 내야 한다.**
   - Box에 면별 색을 지정할 수 있고, Cylinder, Hemisphere, Cone이 있다.
   - 하지만 조명이 없다. Hemisphere가 평면 톤 하나로 렌더링되었다.
   - 각 도형의 중심 z로 정렬한다.
   - GitHub 릴리스 1.1.1은 2019년(npm 1.1.3은 2022년)이고, 저장소 마지막 push는 2023년이다.
6. **three.js SVGRenderer는 실제 메시를 렌더링하지만 출력이 삼각형 수프다.**
   - 코어 저장소에 있고 여전히 유지보수된다(성능 수정 2026-03-21, Sprites/SVGObjects 깊이 정렬 2025-11).
   - OrthographicCamera로 실제 메시를 렌더링한다. 삼각형마다 Lambert 조명을 주고, 이음새를 가리는 'overdraw'와 스타일이 같은 연속 패스 병합을 지원한다.
   - 출력은 삼각형 단위로 정렬된 삼각형 수프다. 203X 룩을 내려면 색 양자화와 병합 단계(예: 같은 톤 삼각형을 Paper.js unite로 합치기)가 필요하다.
   - 아치가 많은 복잡한 콜로세움 타원에 가장 알맞다. 기초 컷어웨이에는 three-bvh-csg와 함께 쓴다.
7. **정밀 CAD·은선 도구는 면이 아니라 선을 만든다.**
   - CadQuery, build123d, Asymptote, fogleman/ln, three-svg-renderer 윤곽선이 여기에 해당한다. 203X의 평면 채움을 주된 룩으로 만들기에는 맞지 않지만, 정확한 키라인이나 단면 윤곽을 공급할 수는 있다.
   - OpenSCAD의 projection()은 XY 평면으로만 평탄화한다(실루엣 또는 슬라이스).
   - TikZ/tikz-3dplot에는 은면 제거가 없다(CTAN 버전 2012-01-11).
8. **타이포그래피 쪽에는 Typst v0.15.1 + CeTZ v0.5.3이 가장 좋은 코드 기반 OSS 선택지다.** 정보 패널, 연표, 3단계 균열 치유 단면이 여기에 해당한다.
   - CeTZ의 ortho()는 기본값이 아이소메트릭(x 35.264°, y 45°)이다. drawable 정렬과 선택적 cull-face가 있고, 0.5.1부터 패스 불리언 연산을 지원한다.
   - Typst는 PDF/SVG를 내보내고 CJK 폰트를 처리한다. 한글 셰이핑은 이번에 테스트하지 않았다.
   - Typst와 TeX 모두 로컬에 설치되어 있지 않다.
9. **성능은 제약이 아니다. 실제 한계는 Figma 레이어 수다.**
   - 상자 3000개를 그리는 데 elchininet은 202 ms(패스 9000개, 2.5 MB), anatomy 키트는 50 ms(패스 18000개, 2.0 MB)가 걸렸다.
   - anatomy는 솔리드 하나당 패스를 약 6개(fill, shades, top, crease, outline) 내므로, Figma로 가져오기 전에 병합하거나 평탄화해야 한다.
10. **에이전트 스킬 생태계(2026)에 인쇄 포스터용은 없다.**
    - anatomy 외에 MrBongoC/ai-iso-skill(191 stars, MIT), DrishtantKaushal/IsometricAnimation(ai-iso-skill과 Hairline을 크레딧에 표기), N3R01N/iso-building-generator(시드 기반 절차적 아이소메트릭 SVG 건물, npm 1.0.0), lucasmarkes/hairline(선 전용)이 있다.
    - 모두 인터랙티브 HTML/SVG 설명물을 만든다. 인쇄 포스터나 사람·군중을 겨냥한 것은 없다.
    - 따라서 인부 인물은 여전히 소형 심볼 라이브러리로 직접 작성해야 한다.
11. **경로 메모(정정):** 조사 시점에 `/Users/um-yunsang/roman-concrete-private-refs/.planning/2026-10-18-203x-benchmark/originals`가 디스크에 없었다. 조사 도중 사용자 지시로 이전 작업 폴더가 삭제되었기 때문이며, 정상이다. `docs/references/203x-benchmark.md`도 조사 시점에 디스크에 없었다. 203X 원본 크롭은 현재 `/Users/um-yunsang/roman-concrete-private-refs/docs/references/assets/203x/originals/`에 있다.

## 2.3 권장 파이프라인

1. **주 건축물에서는 래스터→트레이싱 방식(사용자가 폐기한 이전 작업)을 중단한다.**
   - AI 이미지와 Blender 이미지는 참고용으로만 둔다.
   - 각 랜드마크를 하나의 Bun/TS 씬 모듈 안에서 파라메트릭 솔리드로 작성한다. 기하·음영 코어로는 Anatomy 키트(`kit/iso-kit.mjs` + `kit/lathe.mjs`)를 쓴다.
   - 선택적으로 Anatomy 스킬 전체를 설치해, 에이전트가 부품 목록, 근접 QA, 감사 워크플로를 따르게 한다.
2. **포스터 전체에 카메라를 하나만 쓴다.** fitProjection을 elevation 30, azimuth 45로 고정한다. 203X처럼 2:1 다이메트릭이 된다. 랜드마크별 스케일은 따로 정하되 축은 절대 바꾸지 않는다.
3. **기하 레시피**
   - Pantheon: cylinder()로 드럼을 만든다. 반구는 부드러운 [s,r,1] knot를 준 solidOf()로 만든다(포스터화 밴드, 확인됨). 격자천장 링과 오큘러스 링에는 arcOf()/ribsOf()를 쓴다.
   - Colosseum: 층마다 타원형 extrude() 링을 쌓는다. 아케이드는 아치 개구부가 있는 벽면으로 만든다. 개구부는 타원 호(@elchininet/isometric의 curveTo가 내는 것과 같은 방식)로 그리거나, 투영된 면에 Paper.js subtract를 적용해 뚫는다.
   - 기초·균열 컷어웨이: 투영된 면에 Paper.js intersect/subtract를 쓰거나, 3D 단계에서 three-bvh-csg를 쓴다. 절단면에는 고유한 평면 톤을 준다.
   - 수도교, Portus, Pompeii 유적: slabOf/extrude에 수로·파이프용 `tube.mjs`를 더한다.
4. **음영**
   - 재질마다 면 톤 3개(top, 밝은 측면, 어두운 측면)와 곡면용 밴드 톤 최대 1개를 정한다.
   - 키트의 shade 버킷을 이 톤들에 매핑한 다음, 명시적 fill/stroke 속성으로 굽는다(CSS var() 없음, `<style>` 없음).
   - 이 단계는 필수다. 굽지 않은 SVG는 rsvg-convert에서 전부 검게 렌더링되었다.
5. **깊이**
   - 객체는 depthOf(centre)로 정렬하고, 각 객체 내부의 순서는 고정한다.
   - 서로 맞물린 부분(링 안의 경기장 바닥, 비계 안의 인부)은 뒤 조각과 앞 조각으로 나눈다.
   - 가능하면 Anatomy recorder/audit(`node build.mjs --audit`)를 쓴다.
6. **인물·소품**
   - 2~3톤 아이소메트릭 인부·소품 심볼(석회 가마, 혼합 통, 암포라, 크레인, 수레)의 소형 라이브러리를 손으로 작성한다.
   - 재사용 그룹이나 `<symbol>`/`<use>`로 내보낸다(svg.js/svgdom 또는 일반 문자열). 반대 축용으로는 미러링한다.
7. **조립·내보내기**
   - 각 랜드마크와 레이어에 고정된 id나 그룹 이름을 준다.
   - 솔리드마다 쌓인 약 6개의 패스를 평탄화해(Paper.js unite/divide 또는 Shapely) Figma 레이어 수를 줄인다.
   - 씬마다 SVG를 하나씩 내보내 Figma로 가져간다. 텍스트 레이어는 Figma에 둔다.
   - 정보 패널, 차트, 지도는 D3로 만든다. 코드로 조판한 패널을 원하면 Typst+CeTZ를 쓴다.
8. **QA 루프**
   - A2 인쇄 스케일로 rsvg-convert 렌더를 하고, 확대 크롭도 함께 본다.
   - `var(`, 떠도는 작은 패스, 객체별 색 수를 린트한다.
   - 선택적으로 헤드리스 Chrome에서 Anatomy의 `scripts/capture.mjs`와 `lines.mjs`를 실행한다.
   - 203X 크롭과 비교하며 랜드마크별로 반복한다.

## 2.4 실제로 실행한 검증·시험과 결과

1. **설치**: `mkdir -p /private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/iso-smoke && cd there && bun add @elchininet/isometric@4.0.0 zdog@1.1.3 jsdom`
   - 결과: 패키지 50개, 2.19 s, node_modules 38 MB.
   - @elchininet/isometric이 자체 jsdom을 번들하므로, 최상위 jsdom은 필요 없었다.
2. **@elchininet/isometric import 오류와 해결**: `bun elchi.mjs`('@elchininet/isometric/node' 정적 import)가 `esm/index.node.js`에서 'ReferenceError: window is not defined'로 실패했다. node v26.7.0에서도 같은 오류가 났다.
   - 해결: `globalThis.window = undefined;`를 설정한 뒤 `await import('@elchininet/isometric/node')`로 불러온다.
   - 결과: 패스 9개가 생성되었고, curveTo가 진짜 SVG 타원 호('A 73.484684 42.426392 -119.999977 0 1 553.923 350')를 냈다.
3. **@elchininet/isometric 렌더 확인**: `rsvg-convert -w 900 elchi.svg -o elchi.png`로 렌더하고 Read로 보았다.
   - 빨간 바탕 위에 3톤 아이소메트릭 상자, 그리고 타원형 아치 개구부와 어두운 아치 안쪽면(intrados), 교각 측면을 가진 아치 벽이 그려졌다.
   - 가장자리가 깨끗하고 선명했다.
   - 파일: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/iso-smoke/elchi.png`
4. **Zdog**: `bun zdog.mjs`를 실행했다(jsdom document, `<svg>`에 Zdog.Illustration, rotate x=-atan(1/√2), y=TAU/8, `illo.updateRenderGraph()`). 패스 12개가 나왔다.
   - rsvg-convert로 확인한 결과: 면별 색이 들어간 상자, 원통 드럼과 Hemisphere 돔이 그려졌다. 돔은 평면 톤 하나뿐이다(조명 없음). 평면 아치 윤곽에는 깊이가 없다.
   - 파일: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/iso-smoke/zdog.png`
5. **Anatomy 키트(굽기 전)**: 키트 소스만 가져왔다. `gh api repos/wheresryan22/anatomy/contents/kit/{iso-kit.mjs,lathe.mjs,iso.css} -H 'Accept: application/vnd.github.raw'`(91 KB)로 scratchpad/anatomy-kit/kit에 받았다.
   - `bun dome.mjs`를 실행했다(slabOf 상자 + cylinder 드럼 + 부드러운 knot를 준 solidOf 반구, depthOf 정렬, figureSvg standalone light). 패스 23개가 나왔다.
   - 톤이 `<style>` 안의 CSS var()이기 때문에 rsvg-convert가 전부 검게 렌더링했다.
6. **Anatomy 키트(구운 뒤)**: 클래스를 fill 속성으로 구웠다. iso-fill/iso-shade[0-3]/iso-top/iso-line을 테라코타 팔레트에 매핑하고 `<style>`을 제거했다.
   - rsvg-convert로 확인한 결과: 슬래브, 4밴드 원통, 부드럽게 포스터화된 돔이 깔끔하게 렌더링되었다. 203X의 밴드 진 곡면에 가장 가까운 룩이다.
   - 돔의 톤 경계 하나가 약간 흔들렸다.
   - 파일: `/private/tmp/claude-501/-Users-um-yunsang-roman-concrete-private-refs/2898b239-f072-41ad-9a54-5ea0cf39c626/scratchpad/anatomy-kit/dome-baked.png`
7. **성능**(각 디렉터리에서 `bun perf.mjs`)
   - @elchininet/isometric: 상자 3000개에 202 ms(패스 9000개, SVG 2.5 MB).
   - Anatomy 키트: slabOf 솔리드 3000개와 깊이 정렬에 50 ms(패스 18000개, SVG 2.0 MB).
8. **설치 용량**: 스크래치 설치 총량은 약 38 MB로 50 MB 예산 이하다. 전역 설치는 하지 않았고, 프로젝트 파일도 수정하지 않았다.

## 2.5 후보 도구 표

적합도 높은 순으로 정렬했다. 적합도가 같으면 원문 순서를 따랐다.

| 이름 | 단계 | 하는 일 | 적합도(1~5) | 라이선스 | 오픈소스 여부 | 유지보수 상태 | 주의사항 | URL |
|---|---|---|---|---|---|---|---|---|
| Anatomy (Agent Skill + iso-kit) | agent-skill / vector-authoring / harness-QA | Claude Code 스킬과 무의존 JS 키트. 작은 음영 솔리드를 많이 모아 아이소메트릭 형상을 만듦: slabOf/extrude/cylinder 각기둥, 부드러운 밴드 톤을 가진 lathe/solidOf/sphereOf 회전체, 곡면 위 arcOf/ribsOf 선, tube.mjs 파이프. 부품은 depthOf에 따라 뒤에서 앞으로 칠함. audit.mjs가 깊이 순서와 간격을 검증하고, capture.mjs, drive.mjs, lines.mjs가 헤드리스 Chrome QA를 수행. 출력은 standalone SVG, HTML, React | 4 | MIT | 예 | v1.1.0 릴리스 2026-10-12, push 2026-10-15, 15,206 stars, 1,165 forks | standalone SVG가 `<style>`과 CSS var() 톤을 써서 rsvg-convert에서 전부 검게 렌더링됨. 색을 fill 속성으로 구워야 함(스모크 테스트에서 수행). 아치 개구부나 오목한 수직면 프리미티브가 없음: extrude는 수직 바닥 윤곽 각기둥이고 prismOf는 볼록 다각형만 받으므로, 아케이드는 별도 코드나 Paper.js 불리언이 필요함. 솔리드당 패스 약 6개라 Figma 전에 평탄화할 것. 전체 빌드와 감사는 설계상 느림. 3D turn 모드는 베타 | https://github.com/wheresryan22/anatomy |
| Paper.js (paper / paper-jsdom) | vector-authoring / boolean cut-aways / cleanup | 곡선 정확도를 유지하는 불리언 연산(unite, intersect, subtract, exclude, divide, resolveCrossings)과 SVG 가져오기·내보내기를 갖춘 벡터 스크립팅 | 4 | MIT (npm 기준, GitHub API는 NOASSERTION) | 예 | 저장소 마지막 push 2024-07-23, npm paper 0.12.18(2024-07-17), 15,087 stars, paper-jsdom 저장소는 아카이브됨 | 유지보수가 느려짐(2024-07 이후 push 없음). 이번에 스모크 테스트하지 않음. 'paper' npm 패키지는 압축 해제 시 약 12 MB | https://github.com/paperjs/paper.js |
| @elchininet/isometric | vector-authoring | TypeScript 라이브러리. TOP/FRONT/SIDE 평면 위의 IsometricRectangle/Circle/StarPolygon/Path/Text/Group을 담는 IsometricCanvas. (right,left,top) 아이소메트릭 좌표의 M/L/C 패스 명령. `getSVGCode()`가 SVG를 반환. Node 엔트리는 jsdom 사용 | 3 | Apache-2.0 | 예 | v4.0.0 릴리스 2026-03-29, 저장소 push 2026-10-11, 242 stars | v4.0.0 '/node' ESM 빌드가 Bun 1.3.14와 Node 26.7에서 'ReferenceError: window is not defined'를 던짐. 우회책: `globalThis.window = undefined` 후 dynamic import. 자동 깊이 정렬과 조명 없음. 요소마다 무작위 id가 붙음(Figma 레이어용으로 이름을 바꿀 것) | https://github.com/elchininet/isometric |
| three.js SVGRenderer + OrthographicCamera | flat-render (3D mesh to SVG) | three.js 씬을 SVG 삼각형으로 투영. Projector가 삼각형 단위로 정렬(화가 알고리즘). Lambert/Phong/Standard 재질을 면 단위로 조명. 'overdraw'가 삼각형을 넓혀 이음새를 숨김. 스타일이 같은 연속 패스를 병합. setPrecision. SVGObject로 라벨 같은 원시 SVG 노드를 깊이 정렬과 함께 삽입 | 3 | MIT | 예 | three r186(npm 0.186.1, 2026-09-24). SVGRenderer 커밋 2026-03-21(성능 수정), 2025-11-07(sprites/SVGObjects 깊이 정렬). 116,555 stars | 삼각형 중심 기준 정렬은 분할을 하지 않아 교차하는 면이나 긴 면에서 실패할 수 있음. 매끈한 메시는 톤이 많아지므로 재질당 3톤으로 직접 양자화해야 함. 병합 전 출력이 패스 수만 개에 이를 수 있음. 이번에 스모크 테스트하지 않음 | https://github.com/mrdoob/three.js/blob/dev/examples/jsm/renderers/SVGRenderer.js |
| three-bvh-csg | modeling (boolean cut-aways in 3D) | three-mesh-bvh를 이용해 three.js 메시에 빠른 CSG(union, subtract, intersect) 수행 | 3 | MIT | 예 | push 2026-09-27, npm 0.0.18, 951 stars | 1.0 이전 버전. three.js SVGRenderer나 별도 투영기와 함께 써야만 쓸모가 있음. 테스트하지 않음 | https://github.com/gkjohnson/three-bvh-csg |
| Typst + CeTZ | layout / typography / diagrams | Typst는 PDF/SVG를 내보내는 마크업 조판 시스템. CeTZ는 그 드로잉 라이브러리로, ortho()(기본 아이소메트릭 x=35.264°, y=45°, drawable 정렬, cull-face), perspective(), 패스 boolean() 연산(0.5.1부터), svg-path 요소를 제공 | 3 | Typst Apache-2.0, CeTZ LGPL-3.0 | 예 | Typst v0.15.1(2026-07-17), 56,682 stars. CeTZ v0.5.3(2026-10-16), 1,860 stars | CeTZ는 drawable 단위로 정렬(면 분할 없음). 텍스트 레인은 Figma 레이어를 쓸 계획이라 Typst가 Figma와 역할이 겹침. 한글 폰트 셰이핑 미테스트 | https://github.com/cetz-package/cetz |
| SVG.js + svgdom | assembly / symbol reuse | 가벼운 SVG DOM 구성·조작(그룹, symbol/use, defs, 변환). svgdom이 Node/Bun용 헤드리스 DOM을 제공 | 3 | MIT (npm 기준, GitHub API는 NOASSERTION), svgdom MIT | 예 | svg.js npm 3.2.8(2026-08-04), 11,832 stars. svgdom push 2026-09-09, 297 stars | 3D 없음. Figma가 `<use>` 인스턴스를 유지하는지 사본으로 펼치는지 확인하지 않음 | https://github.com/svgdotjs/svg.js |
| D3 (d3-shape, d3-scale, d3-geo) | charts / maps for info panels | 데이터 기반 SVG 생성: 차트, 스케일, 지리 투영(예: 지중해/Portus 위치 지도) | 3 | ISC | 예 | push 2026-05-28, 113,768 stars | Node에서는 DOM이 필요하거나, d3-path로 문자열 출력을 해야 함 | https://github.com/d3/d3 |
| Shapely | geometry post-process (polygon booleans) | 2D 다각형에 대한 Python 불리언, buffer, union 연산 | 3 | BSD-3-Clause | 예 | push 2026-10-16, 4,527 stars | 폴리라인만 다루므로 호는 조밀하게 쪼개야 함(다시 맞추지 않으면 곡선이 사라짐). Paper.js는 베지어를 유지함 | https://github.com/shapely/shapely |
| Zdog | vector-authoring (pseudo-3D) | canvas나 SVG로 렌더링하는 의사 3D 엔진. Box(면별 색), Cylinder, Cone, Hemisphere, Ellipse, arc/bezier 패스 명령을 쓰는 Shape. 회전으로 아이소메트릭 뷰를 만듦 | 2 | MIT (README 기준, GitHub API는 없음으로 표시) | 예 | 마지막 GitHub 릴리스 v1.1.1(2019-10-23), npm 1.1.3(2022-05), 마지막 push 2023-07-18, 10,672 stars | 음영은 도형을 추가해 흉내 내야 함. 불리언과 은면 분할이 없음 | https://github.com/metafizzy/zdog |
| three-svg-renderer (LokiResearch) | flat-render (hidden-line vector) | 메시 모서리의 viewmap을 만들어 채움 다각형, 보이는 윤곽선, 숨은 윤곽선을 패스별로 출력하는 실험적 three.js 렌더러 | 2 | GPL-3.0 | 예 | npm 1.0.4, 마지막 push 2023-05-29, 62 stars | README에 'experimental'이라고 되어 있고 문서는 작성 중. 테스트하지 않음 | https://github.com/LokiResearch/three-svg-renderer |
| svg3d (janbridley) | flat-render (Python mesh to SVG) | prideout/svg3d를 Python으로 다시 쓴 것. DiffuseShader/UniformShader와 View.isometric/dimetric/trimetric 프리셋으로 메시나 다면체를 SVG로 렌더링 | 2 | MIT | 예 | push 2026-10-16, 6 stars(원본 prideout/svg3d: 375 stars, push 2024-07) | 문서 페이지에 은면 처리나 깊이 정렬 방식이 설명되어 있지 않음. 테스트하지 않음 | https://github.com/janbridley/svg3d |
| ai-iso-skill | agent-skill | 단일 HTML 파일에 인터랙티브 아이소메트릭 형상을 그리는 Claude 스킬 | 2 | MIT | 예 | push 2026-10-04, 191 stars | 인터랙티브 웹 중심. README와 품질을 깊이 살펴보지 않음 | https://github.com/MrBongoC/ai-iso-skill |
| IsometricAnimation (agent skill) | agent-skill | 인터랙티브 아이소메트릭 SVG 객체와 씬을 HTML로 만드는 에이전트 스킬(예시 46개, 예: 24층 오피스 타워). ai-iso-skill과 Hairline을 크레딧에 표기 | 2 | MIT | 예 | push 2026-10-07, 1 star | 품질 미확인 | https://github.com/DrishtantKaushal/IsometricAnimation |
| iso-building-generator | generation (procedural isometric SVG) | 스타일 팩과 /kit 툴킷을 갖춘, 시드 기반 절차적 아이소메트릭 SVG 건물 생성기. 무의존. SVG 안에 CSS 애니메이션 포함 | 2 | MIT | 예 | npm 1.0.0(2026-08-03), 0 stars | 새로 나와 검증되지 않음. 인쇄용으로는 내장 CSS 애니메이션을 제거해야 함 | https://github.com/N3R01N/iso-building-generator |
| Asymptote | flat-render (3D vector) | TeX와 연동되는 2D/3D 벡터 언어. 'bsp' 모듈이 평면 면에 대해 이진 공간 분할(BSP) 은면 제거를 하고, render=0이면 조각별 평면 곡면을 투영된 벡터(EPS/PDF) 3D로 출력 | 2 | GPL-3.0 (GitHub API 기준) | 예 | push 2026-10-18, 690 stars | 설치가 무거움(TeX). render=0에서 곡면은 벡터로 출력되지 않음. 3D 문서 페이지에 SVG 출력 언급이 없음 | https://github.com/vectorgraphics/asymptote |
| build123d | modeling + HLR keylines | OCCT 기반 Python CAD. 정확한 솔리드와 불리언. Shape.project_to_viewport가 보이는 모서리와 숨은 모서리를 반환. ExportSVG가 레이어별 SVG를 씀(fill_color는 2D 면에 적용) | 2 | Apache-2.0 | 예 | push 2026-10-17, 3,448 stars | OCCT 휠이 큼(50 MB 예산을 크게 넘을 것으로 보이나 측정하지 않음). 채움을 쓰려면 다각형화와 면별 톤 조회가 필요함 | https://github.com/gumyr/build123d |
| CadQuery SVG exporter | modeling + HLR keylines | OCCT 기반 CAD. SVG 내보내기가 은선 제거(projectionDir, showHidden, strokeColor/hiddenColor)를 쓰며 fill='none' 선화를 출력 | 2 | GitHub API: NOASSERTION (추가 확인 안 함) | 예 | push 2026-10-10, 5,952 stars | OCP 의존성이 무거움. 선 전용 출력 | https://github.com/CadQuery/cadquery |
| ln (fogleman) | flat-render (hidden-line) | 광선 기반 은선 제거, 프리미티브(sphere, cube, cylinder, cone), CSG(intersection, difference, union), SVG/PNG 출력을 갖춘 Go 3D 선화 엔진 | 2 | MIT | 예 | 마지막 push 2019-07-19, 3,471 stars | Go 툴체인 필요. 채움 없음 | https://github.com/fogleman/ln |
| Isomer | vector-authoring (canvas) | Prism, Pyramid, Cylinder, Stairs, 압출 Path와 광원 방향에 따른 자동 면 채색을 갖춘 아이소메트릭 라이브러리 | 2 | MIT | 예 | npm 0.2.6, 마지막 push 2022-04-20, 2,906 stars | SVG로 내려면 canvas→SVG 컨텍스트 shim이 필요함(미확인). 그리는 순서는 수동 | https://github.com/jdan/isomer |
| OpenSCAD | modeling | 스크립트 기반 CSG 모델러. projection()이 XY 평면으로 평탄화(실루엣 또는 cut=true 슬라이스)해 2D SVG/DXF로 내보냄 | 1 | GitHub API: NOASSERTION (추가 확인 안 함) | 예 | push 2026-10-18, 10,461 stars | 면별 채움이나 은면 출력이 없음 | https://github.com/openscad/openscad |
| TikZ + tikz-3dplot | vector-authoring (TeX) | 3D 뷰와 구면 극좌표 플롯을 위한 TikZ 좌표 변환 | 1 | LPPL 1.3 | 예 | CTAN 버전 2012-01-11 | 그리는 순서를 전부 수동으로 정해야 함 | https://ctan.org/pkg/tikz-3dplot |
| Penrose | layout (constraint-based 2D diagrams) | Domain/Substance/Style 표기로부터 최적화 기반 레이아웃(예: AutoLabel)을 써서 SVG 다이어그램을 생성 | 1 | MIT | 예 | v3.3.1(2026-08-30), 7,993 stars | README에 3D나 아이소메트릭 지원이 없음 | https://github.com/penrose/penrose |
| obelisk.js | pixel isometric (canvas) | canvas 위에 아이소메트릭 픽셀아트 객체(cube, brick, pyramid, slope)를 만듦 | 1 | MIT (npm 기준) | 예 | 마지막 push 2019-06-29, 2,325 stars | 래스터 전용 | https://github.com/nosir/obelisk.js |
| Hairline | assets (isometric line figures) | React/DOM용 인터랙티브 아이소메트릭 선화 형상 33종(의존성 없음) | 1 | MIT | 예 | push 2026-10-14, 2,238 stars | 참고 이상의 관련성은 없음 | https://github.com/lucasmarkes/hairline |

### 2.5.1 후보별 보충 정보 (적합도 근거, 에이전트 구동, 로컬 설치, 근거 URL)

**Anatomy (Agent Skill + iso-kit)**
- 적합도 근거: 203X의 선명한 평면 음영 아이소메트릭 부품에 가장 가까운 OSS다.
  - 평면 면에는 4단계 버킷 음영을, 돔과 드럼에는 포스터화 밴드를 준다. 판테온과 비슷한 드럼과 돔으로 확인했다.
  - 진짜 아이소메트릭 카메라, 감사 기능, 에이전트용으로 만든 스크린샷 QA 루프가 있다.
  - 5점이 아닌 이유: 기계에 맞춰져 있다(README: 'Not people or exact maps'). 톤이 단색 CSS var()라 다시 색칠하고 구워야 한다. 아케이드와 컷어웨이는 별도 기하가 필요하다.
- 에이전트 구동: Agent Skill(`/anatomy`)과 일반 ESM 키트. Bun으로 `kit/iso-kit.mjs`와 `kit/lathe.mjs`를 직접 실행했다.
- 로컬 설치: 아니오. 키트 파일 3개만 스크래치패드로 가져왔다(91 KB).
- 근거 URL: https://github.com/wheresryan22/anatomy · https://github.com/wheresryan22/anatomy/blob/main/references/kit.md · https://skills.wheresryan.sh/anatomy

**Paper.js**
- 적합도 근거: 코드 경로에서 빠진 조각을 채운다.
  - 아치 개구부: 벽면에서 윗부분이 반원인 사각형을 뺀다.
  - 콘크리트 기초와 균열 컷어웨이: 단면 상자와 교차시킨다.
  - 같은 톤의 삼각형이나 면을 하나의 깔끔한 영역으로 병합한다.
  - Figma로 넘기기 전에, 화가 알고리즘 순서로 겹친 도형을 서로 겹치지 않는 도형으로 평탄화한다.
- 에이전트 구동: npm 라이브러리(paper-jsdom 래퍼나 paper + jsdom으로 Node에서 실행).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/paperjs/paper.js/blob/develop/src/path/PathItem.Boolean.js · https://github.com/paperjs/paper-jsdom

**@elchininet/isometric**
- 적합도 근거: 아치와 원에 진짜 타원 호를 쓰는 깔끔한 SVG를 낸다(확인함). 면별 채움을 명시해 코드로 다루기 쉽다. 음영 톤과 그리는 순서는 직접 정해야 하고, 솔리드나 불리언은 없다.
- 에이전트 구동: Bun/Node에서 스크립팅하는 npm 라이브러리.
- 로컬 설치: 예. 스크래치패드에만 설치했다(iso-smoke, v4.0.0).
- 근거 URL: https://github.com/elchininet/isometric · https://www.npmjs.com/package/@elchininet/isometric

**three.js SVGRenderer + OrthographicCamera**
- 적합도 근거: 에이전트가 실제 3D 기하(아치가 많은 타원형 콜로세움, 판테온 격자천장)를 하나의 일관된 직교 아이소메트릭 카메라로 만들고, 벡터 면으로 받을 수 있다. 컷어웨이용 three-bvh-csg, 색 양자화, Paper.js 병합 단계를 더하면 깔끔한 3톤 출력에 이를 수 있다. 원본 출력은 삼각형 수프다.
- 에이전트 구동: npm 라이브러리. DOM이 필요하다(브라우저, 또는 Bun에서 jsdom/linkedom).
- 로컬 설치: 아니오. three는 압축 해제 시 약 20 MB라 예산을 지키려고 건너뛰었다.
- 근거 URL: https://github.com/mrdoob/three.js/blob/dev/examples/jsm/renderers/SVGRenderer.js · https://threejs.org/examples/#svg_sandbox

**three-bvh-csg**
- 적합도 근거: 콜로세움 기초 컷어웨이와 균열 단면을 SVG 투영 전에 진짜 3D 불리언으로 만든다. 그래서 절단면이 자동으로 고유한 평면 톤을 갖게 된다.
- 에이전트 구동: npm 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/gkjohnson/three-bvh-csg

**Typst + CeTZ**
- 적합도 근거: 정보 디자인 쪽(여백 패널, 연표, 번호 매긴 공정, 한글 본문)과 3단계 균열 치유 단면 다이어그램에 가장 좋은 코드 기반 OSS 도구다. 빽빽한 중앙 아이소메트릭 아트를 맡기기에는 너무 제한적이다.
- 에이전트 구동: 일반 텍스트 소스로부터 CLI(`typst compile`).
- 로컬 설치: 아니오(typst가 없음).
- 근거 URL: https://github.com/typst/typst · https://github.com/cetz-package/cetz/blob/master/src/draw/projection.typ · https://github.com/cetz-package/cetz/blob/master/src/draw/boolean.typ

**SVG.js + svgdom**
- 적합도 근거: 포스터 SVG를 조립하는 데 유용하다. 랜드마크마다 이름 붙은 그룹을 만들어 Figma 레이어로 쓰고, 작은 인부와 소품을 `<symbol>` 라이브러리로 만들어 `<use>`로 재사용하고, 미러링한 변형을 만든다.
- 에이전트 구동: npm 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/svgdotjs/svg.js · https://github.com/svgdotjs/svgdom

**D3**
- 적합도 근거: 203X식 여백 패널(비교 차트, 시간에 따른 강도 곡선, 제국 지도)에 맞는다. 아이소메트릭 아트용은 아니다.
- 에이전트 구동: npm 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/d3/d3

**Shapely**
- 적합도 근거: 이미 설치되어 있다. 컷어웨이를 위해 투영된 면 다각형을 자르고, 화가 알고리즘 순서로 겹친 부분을 서로 겹치지 않는 영역으로 평탄화하고, 같은 톤의 조각을 합칠 수 있다.
- 에이전트 구동: Python 라이브러리/스크립트.
- 로컬 설치: 예(시스템 python3에 shapely 2.1.2).
- 근거 URL: https://github.com/shapely/shapely

**Zdog**
- 적합도 근거: jsdom과 함께 Bun에서 작동함을 확인했다(면 색 3개의 상자, 원통 드럼, 반구 돔, 평면 아치 윤곽). 하지만 다음 이유로 2점이다.
  - 조명이 없다(돔이 평면 톤 하나).
  - 도형 중심 기준으로 정렬한다.
  - 평면 도형에 두께가 없다.
  - 둥근 스트로크 미감이 장난감 같다.
  - 유지보수되지 않는다.
- 에이전트 구동: npm 라이브러리. `<svg>` 요소에 렌더링한다(jsdom으로 DOM 필요).
- 로컬 설치: 예. 스크래치패드에만 설치했다(iso-smoke, zdog 1.1.3).
- 근거 URL: https://github.com/metafizzy/zdog · https://zzz.dog/

**three-svg-renderer (LokiResearch)**
- 적합도 근거: 실제 3D에서 영역 채움과 깔끔한 윤곽선을 함께 얻는다는 개념은 맞는 출력이다. 하지만 실험적이고 오래 방치되었다. 코드를 배포한다면 GPL-3.0도 걸림돌이다.
- 에이전트 구동: npm 라이브러리(async `generateSVG`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/LokiResearch/three-svg-renderer

**svg3d (janbridley)**
- 적합도 근거: 아이소메트릭 프리셋을 갖춘, 메시를 평면 SVG로 바꾸는 단순한 경로다. 과학 도판용이고, 아주 초기 프로젝트다.
- 에이전트 구동: Python 라이브러리(`pip install svg3d`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/janbridley/svg3d · https://svg3d.readthedocs.io/ · https://github.com/prideout/svg3d

**ai-iso-skill**
- 적합도 근거: 에이전트 네이티브 아이소메트릭 SVG 워크플로다. IsometricAnimation이 바탕으로 삼은 면 로컬(face-local) 투영 방식을 제공했다. Anatomy보다 작고 덜 성숙하다.
- 에이전트 구동: Agent Skill.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/MrBongoC/ai-iso-skill

**IsometricAnimation**
- 적합도 근거: 건물 씬 예시가 Anatomy의 기계보다 도시 지도 콘텐츠에 가깝다. 하지만 검증되지 않았고(1 star) 인터랙티브 웹 지향이다.
- 에이전트 구동: Agent Skill(Codex / Claude Code).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/DrishtantKaushal/IsometricAnimation

**iso-building-generator**
- 적합도 근거: 사용자 정의 'roman' 스타일 팩을 만들어 채움용 건물(Pompeii 거리, Portus 창고)을 얻는 아이디어와 코드의 공급원으로 쓸 수 있다.
- 에이전트 구동: npm 라이브러리(`generateBuilding(seed, {style})`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/N3R01N/iso-building-generator

**Asymptote**
- 적합도 근거: 평면 면의 은면을 정확히 분할하는 진짜 3D라 기술적으로는 강하다. 하지만 문서에 따르면 벡터 3D 지원이 제한적이고('limited support for hidden surface removal, lighting'), TeX 툴체인이 필요하다.
- 에이전트 구동: CLI(asy) 스크립팅 언어.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/vectorgraphics/asymptote · https://asymptote.sourceforge.io/doc/three.html

**build123d**
- 적합도 근거: 정확한 아치, 돔, 단면 절단과 정밀한 가시 모서리를 얻을 수 있다. 하지만 3D 투영 결과가 음영 채움이 아니라 선이다. 203X 룩에서는 키라인이나 참고용 생성기로만 쓸 수 있다.
- 에이전트 구동: Python 스크립팅.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/gumyr/build123d

**CadQuery SVG exporter**
- 적합도 근거: 불리언 처리한 솔리드의 정확한 은선 제거 선화를 낸다. 채움은 없다.
- 에이전트 구동: Python 스크립팅 / CLI.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/CadQuery/cadquery/blob/master/cadquery/occ_impl/exporters/svg.py

**ln (fogleman)**
- 적합도 근거: CSG 컷어웨이와 깔끔하고 정확한 은선을 준다. 하지만 선 전용이고 오래 휴면 상태다.
- 에이전트 구동: Go 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/fogleman/ln

**Isomer**
- 적합도 근거: 203X식 아트에 필요한 면별 자동 톤 로직이 있다. 하지만 SVG가 아니라 HTML5 canvas(또는 node-canvas)에만 그린다.
- 에이전트 구동: npm 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/jdan/isomer

**OpenSCAD**
- 적합도 근거: 음영이 들어간 아이소메트릭 출력이 없다. XY 평면 위의 실루엣이나 단면만 주므로, 기껏해야 단면 윤곽의 공급원이다.
- 에이전트 구동: CLI(`openscad -o out.svg`).
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/openscad/openscad · https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/3D_to_2D_Projection

**TikZ + tikz-3dplot**
- 적합도 근거: 은면 제거가 없고, 2012년 패키지이며, TeX 설치가 무겁다.
- 에이전트 구동: CLI로 컴파일하는 LaTeX 소스.
- 로컬 설치: 아니오(tex가 없음).
- 근거 URL: https://ctan.org/pkg/tikz-3dplot

**Penrose**
- 적합도 근거: 2D 수학 다이어그램용이다. 아이소메트릭 일러스트레이션이 아니며, 기껏해야 자동 라벨 배치의 참고가 될 정도다.
- 에이전트 구동: npm(`@penrose/core`) / CLI.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/penrose/penrose

**obelisk.js**
- 적합도 근거: README에 'not for vector isometric graphics'라고 적혀 있다. 출력 유형이 맞지 않는다.
- 에이전트 구동: npm 라이브러리.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/nosir/obelisk.js

**Hairline**
- 적합도 근거: 선 전용 UI 장식이라 채움 포스터 룩이 아니다.
- 에이전트 구동: npm 라이브러리 / shadcn registry.
- 로컬 설치: 아니오.
- 근거 URL: https://github.com/lucasmarkes/hairline
