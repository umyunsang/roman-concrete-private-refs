"""타이틀·패널·푸터 대략 상자(1차 실측 JSON 값에서 출발, 정규 1000x1400 단위).
ink 정밀화는 ra_ink.py가 한다. pad = 탐색 여유(단위).
"""
ZONES = {
 "203x-seoul": {
  "title": ("타이틀 록업(CITY LANDMARK INFOGRAPHICS / SEOUL / City Where Past and Present Coexist)", (340, 62, 662, 252)),
  "panels": [
   ("SUMMARY 요약 정보", "TL", (45, 68, 252, 192)),
   ("Symbol 상징", "TL", (45, 196, 252, 392)),
   ("HISTORY 역사", "TR", (748, 68, 962, 218)),
   ("PERSON IN SEOUL 인물", "BL(하단 띠 좌)", (45, 1172, 245, 1332)),
   ("HANGANG RIVER BRIDGES 한강의 다리", "B(하단 띠 중앙, 가장 넓음)", (255, 1172, 724, 1332)),
   ("FAMOUS CULTURE AREA 문화지역", "BR(하단 띠 우)", (745, 1172, 962, 1332)),
  ],
  "footer": ("푸터(Street H 로고·크레딧·203X)", (40, 1338, 965, 1375)),
 },
 "203x-london": {
  "title": ("타이틀 배너(CITY LANDMARK INFOGRAPHICS / When a man is tired of London… / LONDON)", (312, 38, 952, 198)),
  "panels": [
   ("HISTORY 왕조로 본 역사", "TL", (45, 48, 252, 242)),
   ("WILLIAM MORRIS 윌리엄 모리스", "TL", (45, 243, 252, 338)),
   ("CITY INFORMATION 도시 정보", "TR", (748, 208, 952, 382)),
   ("FAMOUS FESTIVALS 축제", "R(지도 무대 안 오른쪽)", (748, 918, 962, 1202)),
   ("STREET PERFORMANCE 거리공연", "BR(하단 띠 우, 윗변 y1216이 P6·P7과 같음)", (748, 1208, 962, 1332)),
   ("HARRY BECK 해리 벡", "BL(하단 띠 좌)", (45, 1208, 252, 1332)),
   ("BUS LINE 9 9번 버스 노선도", "B(하단 띠 중앙, 버스 지시선이 들어옴)", (325, 1208, 692, 1332)),
  ],
  "footer": ("푸터", (40, 1336, 965, 1375)),
 },
 "203x-berlin": {
  "title": ("타이틀 록업(브란덴부르크 문 액자 + 콰드리가 / Berlin / The City Where the Wall That Divided Germany Fell)", (282, 28, 722, 217)),
  "panels": [
   ("CITY INFORMATION 도시 정보", "TL", (36, 38, 248, 155)),
   ("FAMOUS CULTURE AREA 문화지역(점 격자 위치도+핀 7)", "TL", (36, 175, 258, 348)),
   ("HISTORY 역사", "TR", (742, 38, 962, 182)),
   ("FAMOUS FOOD 유명한 음식", "BL(하단 좌, 코어 판 왼쪽)", (36, 1212, 252, 1338)),
   ("AMPELMANN 암펠만 신호등", "BL(하단 좌, 코어 판 왼쪽)", (276, 1212, 442, 1328)),
  ],
  "footer": ("푸터(203X·Street H 로고·크레딧·QR)", (36, 1342, 965, 1378)),
 },
}
