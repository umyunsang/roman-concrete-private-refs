# v2_map.py 포르투스 변경(이전 → 이후). 원본 d5 로 가져갈 범위: v2_map.py "포르투스" 블록 PORTUS_DX ~ PORTUS_LIGHTHOUSE 와 portus_canal 후처리 두 줄, LANDMARKS L6 의 box·draw_pivot, render.py 의 hexring·portus_params·draw_portus
- PORTUS_DX: -23.76 → 0.0 (더는 쓰지 않음)
- PORTUS_HEX_C: (472.4, 353.64) → (543.1, 312.0)
- PORTUS_BASIN_C: (472.4, 401.64) → (591.1, 312.0)
- PORTUS_HEX_R 24.0, WATER_R 15.2, BASIN_R 21.0 : 그대로
- PORTUS_CANALS 강 쪽: plan_x [470.9, 473.9] · plan_y [322.24, 340.10] → plan_x [511.7, 531.4] · plan_y [310.5, 313.5] (+ "axis":"x")
- PORTUS_CANALS 외항 쪽: plan_x [470.9, 473.9] · plan_y [367.10, 384.60] → plan_x [554.8, 574.06] · plan_y [310.5, 313.5]
  (운하 안쪽 끝은 변 가운데 안쪽 반지름 13.16 안으로 1.5 = 11.7; 뜻이 바뀜: 긴 쪽 = plan_x, 폭 = plan_y)
- PORTUS_EAST_CANAL: plan_x [493.24, 503.24] · plan_y [352, 355] → plan_x [541.46, 544.46] · plan_y [281.16, 291.16] (render 미사용)
- PORTUS_MOLES: arm_a_deg [263, 123] → [173, 33]; arm_b_deg [277, 417] → [187, 327]; colonnade_deg [12, 54] → [282, 324]
- PORTUS_LIGHTHOUSE: plan_angle_deg 78 → 348; screen_base [67.18, 461.95] → to_screen(계산)으로 자동
- 후처리: _c["screen_w_mm"] = (plan_y 폭)·C30, screen_axis = plan_x 양 끝 × plan_y 가운데 (옛: plan_x 폭, plan_y 양 끝)
- LANDMARKS L6: box [5.0, 382.0, 155.0, 474.0] → [150.73, 390.56, 287.09, 484.98]; draw_pivot to_screen(496.16-23.76, 380.0) → to_screen(569.5, 312.0); draw_scale 1.41 그대로
- (선택) L6 form 문구의 옛 각도·좌표는 그대로 남아 있어 원본 d5 에서 문구 갱신 필요
- render.py draw_portus 내용: 육각 꼭짓점 30°+60k 유지(변 가운데가 0°·180°), 성벽 trims {2,5: 가운데 0.42~0.58 비움}, 창고 pieces 변 2·5 (0.06~0.40, 0.60~0.94), 방파제 창고 각 150~210 → 60~120, 운하는 X축 방향으로 그림(ok_hex/ok_out 새 식), canal_info 에 plan_x 추가
