src = open("scripts/wireframe_v16.py", encoding="utf-8").read()
exec(compile(src, "wireframe_v16.py", "exec"))
import time
t0 = time.time()
L = Layer(0, 0, 200, 140, "t", bg=BG + (255,))
# 벽면 라벨 ↘, ↗, 깃대형, 바닥 글자
# 대상: 점
for T, M, mode, side in (((40, 70), M_WALL_UP, "above", "R"), ((120, 90), M_WALL_DN, "above", "L"), ((60, 130), M_WALL_UP, "below", "L")):
    L.rect(T[0] - 8, T[1] - 2, T[0] + 8, T[1] + 6, fill=(190, 150, 100), outline=EDGE)
    draw_label(L, T, ["COLOSSEUM"], "콜로세움 아레나", ["겉은 석회화, 속과 기초는", "콘크리트로 채웠다", "무너짐: 지반·석재 반출·", "관리 부재가 주원인"], C_ARENA_T, M, mode=mode, side=side, sup="Amphitheatrum Flavium")
draw_flag(L, (170, 60), "VESUVIUS", "베수비오", C_SUP_T, M_WALL_UP, side="L")
draw_floor_name(L, 100, 30, "테베레강", "TIBER", RIVER_T, kind="NE")
draw_floor_name(L, 20, 20, "아피아 가도", "VIA APPIA", ROAD_E, kind="SE")
out = L.img.resize((L.w // SS, L.h // SS), Image.LANCZOS)
out.convert("RGB").save("out/v16_work/test1.png")
print("sec", time.time() - t0)
