import sys; sys.stdout.reconfigure(encoding="utf-8")
from mountlex import find_mounts, cm_mounts
cases = [
 ("Canon EF 50mm f/1.8 STM Lens", {"Canon EF"}),
 ("Canon EF-S 18-55mm f/3.5-5.6 IS II", {"Canon EF"}),
 ("Canon 18-135mm f/3.5-5.6 EF-S is STM Lens", {"Canon EF"}),
 ("Canon RF24-105mm F4 L IS USM", {"Canon RF"}),
 ("Canon EOS R7 RF-S18-150mm F3.5-6.3 is STM Lens Kit", {"Canon RF"}),
 ("Yongnuo RF-603 II Wireless Flash Trigger for Canon", set()),
 ("TTArtisan 50mm F1.2 APS-C for Canon M Mount Like M1 M2", {"Canon EF-M"}),
 ("Canon EF-M 22mm f/2 STM", {"Canon EF-M"}),
 ("Sony Alpha SEL1855 E-mount 18-55mm F3.5-5.6 OSS Lens", {"Sony E"}),
 ("Sony FE 24-70mm F2.8 GM", {"Sony E"}),
 ("Sigma 105mm F2.8 DG DN Macro Art (Sony E-mount)", {"Sony E"}),
 ("Rokinon FE75MFT-S 7.5mm F3.5 UMC Fisheye Lens for Micro Four Thirds", {"Micro Four Thirds"}),
 ("Samyang SY85M-S 85mm F1.4 Lens for Sony Alpha", set()),
 ("Nikon AF-S FX NIKKOR 200-400mm f/4G ED VR II", {"Nikon F"}),
 ("Nikon NIKKOR Z 24-70mm f/4 S", {"Nikon Z"}),
 ("Nikon Z 6II Full Frame Mirrorless", {"Nikon Z"}),
 ("Fujinon XF50mmF2 R WR Lens - Silver", {"Fujifilm X"}),
 ("Fujifilm X-T2 Mirrorless Digital Camera", set()),
 ("Fujifilm XF10 Digital Camera", set()),
 ("7artisans 35mm for Fuji X Mount", {"Fujifilm X"}),
 ("Olympus M.Zuiko Digital ED 14-150mm", {"Micro Four Thirds"}),
 ("Olympus 50-200mm Zuiko Digital f/2.8-3.5 ED Lens", {"Four Thirds"}),
 ("Olympus 14-54mm f/2.8-3.5 II AF Zuiko Lens for Olympus Digital SLR", set()),
 ("Fotodiox Lens Mount Adapter Canon EF to Sony E-Mount", {"Canon EF", "Sony E"}),
 ("Pentax K-mount 50mm", {"Pentax K"}),
 ("Pentax K-1 Mark II body", set()),
 ("Neewer 52MM 2x Telephoto Conversion Lens for Nikon D3000", set()),
 ("Panasonic LUMIX G VARIO 14-42mm", {"Micro Four Thirds"}),
 ("Leica M 50mm Summicron", {"Leica M"}),
 ("Meike MK-C-AF4 Macro Extension Tube for Canon EOS EF EF-S", {"Canon EF"}),
]
bad = 0
for t, exp in cases:
    got = set(find_mounts(t))
    ok = got == exp
    bad += not ok
    print(("OK  " if ok else "SAI ") + f"{t[:70]:72s} -> {sorted(got)}" + ("" if ok else f"  (mong {sorted(exp)})"))
print("sai:", bad, "/", len(cases))
for v in ["Canon EF, Canon EF-S", "Sony/Minolta Alpha DT, Sony/Minolta Alpha", "Olympus/Panasonic Micro 4/3",
          "Nikon F(DX), Nikon (DX),Nikon (FX),Nikon F", "Canon", "Sony Alpha", "Nikon 1", "Pentax KAF3, Pentax KAF2",
          "Sony E (NEX)", "Canon RF, Canon EF", "T Mount", "Fujifilm FinePix", "Nikon F (FX)"]:
    print(f"CM {v!r:50s} -> {cm_mounts(v)}")
