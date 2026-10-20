import sys
sys.path.insert(0, "out/v16_work")
import search1
for HUG, XL, CY, PEAK, T in [(23.5, 236, 294.5, 54, 7), (23.5, 236, 296.5, 54, 7), (24, 236, 296.5, 54, 7), (24, 238, 296.5, 54, 7), (23.5, 238, 296.5, 56, 7), (24, 236, 298.5, 56, 7)]:
    print(HUG, XL, CY, PEAK, T, search1.run(HUG, XL, CY, PEAK, T))
