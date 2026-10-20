#!/bin/bash
# 203X(Infographics Lab 203) 도시·지역 포스터 레퍼런스 내려받기 (2026-10-18)
# - 출처: 203x.co.kr 포트폴리오(상세 타일 01/04/05, 960 목업, TN), street-h.com 상품 페이지(전체 포스터 1000x1400)
# - 저장: .work/dl/refs-cities/<slug>/  (받은 파일은 신뢰하지 않는 데이터. 실행 금지, file/크기 확인만)
# - 사용: bash refs_cities_download_203x.sh
set -u
BASE="/Users/um-yunsang/roman-concrete-private-refs/.work/dl/refs-cities"
UA="Mozilla/5.0"

dl() { # slug url
  local slug="$1" url="$2"
  local dir="$BASE/$slug"
  mkdir -p "$dir"
  local name
  name="$(basename "${url%%\?*}")"
  if [ -s "$dir/$name" ]; then echo "skip $slug/$name"; return; fi
  curl -sSL -A "$UA" --max-time 120 -o "$dir/$name" -w "$slug/$name %{http_code} %{size_download}\n" "$url"
}

W="https://203x.co.kr/wp-content/uploads"
S="https://street-h.com/wp-content/uploads"

# 홍콩 (Street H 2022년 4월호) - Street H 쪽 전체 포스터 파일명이 'Tokyo'로 잘못 붙어 있음(홍콩 상품 페이지의 대표 이미지)
dl 203x-hongkong "$S/2022/05/StH_2022_04_Tokyo.jpg"
for n in 01 04 05; do dl 203x-hongkong "$W/2022/07/1000_StH_202204_153_Poster_$n.jpg"; done
dl 203x-hongkong "$W/2022/07/hongkong_960x960.jpg"

# 베를린 (2022년 5월호)
dl 203x-berlin "$S/2022/06/StH_202205_154_berlin_re.jpg"
for n in 01 04 05; do dl 203x-berlin "$W/2022/07/1000_StH_202205_154_poster_re_$n.jpg"; done
dl 203x-berlin "$W/2022/07/berlin_960x960_re.jpg"

# 뉴욕2 센트럴파크 (2022년 9월호)
dl 203x-newyork2-centralpark "$S/2022/10/StH_202209_158_new-york2.jpg"
for n in 01 04 05; do dl 203x-newyork2-centralpark "$W/2022/11/1000_StH_202209_158_poster_$n.jpg"; done
dl 203x-newyork2-centralpark "$W/2022/11/newyork2_960x960.jpg"

# 도쿄 (2021년 5월호)
dl 203x-tokyo "$S/2021/06/StH_2021_05_Poster_Tokyo-1.jpg"
for n in 01 04 05; do dl 203x-tokyo "$W/2021/07/StH_2021_Poster_Tokyo_$n.jpg"; done
dl 203x-tokyo "$W/2021/07/tokyo_960x960.jpg"

# 파리 (2021년 4월호)
dl 203x-paris "$S/2021/05/StH_2021_04_Poster_Paris2.jpg"
for n in 01 04 05; do dl 203x-paris "$W/2021/06/StH_2021_04_Paris_$n.jpg"; done
dl 203x-paris "$W/2021/06/paris_960x960.jpg"

# 상하이 (2020년 12월호)
dl 203x-shanghai "$S/2021/01/shanghai_poster.jpg"
for n in 01 04 05; do dl 203x-shanghai "$W/2020/06/shanghai_1000_$n.jpg"; done
dl 203x-shanghai "$W/2020/06/StH_202012_139_TN.jpg"

# 자금성 (2020년 10월호)
dl 203x-forbiddencity "$S/2020/06/forbidden_city_poster.jpg"
for n in 01 04 05; do dl 203x-forbiddencity "$W/2020/11/StH_202010_137_Poster_$n.jpg"; done

# 타이베이 (2023년 12월호)
dl 203x-taipei "$S/2024/01/StH_2023_12_Poster_re.jpg"
for n in 01 04 05; do dl 203x-taipei "$W/2024/01/1000_StH_2023_12_Poster_re_$n.jpg"; done
dl 203x-taipei "$W/2024/01/taipei_960x960_re.jpg"

# 피라미드 (2024년 4월호)
dl 203x-pyramid "$S/2024/05/StH_2024_04_Poster_re.jpg"
for n in 01 04 05; do dl 203x-pyramid "$W/2024/06/1000_StH_2024_04_Poster_${n}_re.jpg"; done
dl 203x-pyramid "$W/2024/06/pyramid_960x960_re.jpg"

# 런던 (2017년 12월호)
dl 203x-london "$W/2020/06/StH_201712_103_TN.jpg"
for n in 1 4 5; do dl 203x-london "$W/2020/06/1000_32_london_$n.jpg"; done

# 뉴욕 (2018년 3월호)
dl 203x-newyork "$W/2020/06/StH_201803_106_TN.jpg"
for n in 1 4 5; do dl 203x-newyork "$W/2020/07/1000_35_newyork_$n.jpg"; done

# 제주도 (2018년 8월호)
dl 203x-jeju "$W/2020/06/StH_201808_111_TN.jpg"
for n in 1 4 5; do dl 203x-jeju "$W/2020/07/1000_40_jejudo_$n.jpg"; done

# 서울 (2018년 9월호)
dl 203x-seoul "$W/2020/06/StH_201809_112_TN.jpg"
for n in 1 4 5; do dl 203x-seoul "$W/2020/07/1000_41_seoul_$n.jpg"; done

# 청와대 (2022년 7월호)
dl 203x-cheongwadae "$S/2022/08/StH_202206_155_cheongwadae.jpg"
for n in 01 04 05; do dl 203x-cheongwadae "$W/2022/09/1000_StH_2022_07_Poster_$n.jpg"; done

# 그리스·로마 신화 (2023년 6월호) - 로마 관련 주제 확인용
dl 203x-greek-roman-mythology "$S/2023/07/StH_2023_06_Poster-1.jpg"
for n in 01 04 05; do dl 203x-greek-roman-mythology "$W/2023/11/1000_StH_2023_06_Poster_$n.jpg"; done
