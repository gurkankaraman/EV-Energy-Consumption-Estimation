import xml.etree.ElementTree as ET
import pandas as pd
import calculate_elevation

# DataFrame'i al
df = calculate_elevation.extract_shapes_with_z_first_point("eskisehir_last.net.xml")

# 1) Sütun adı 'shape' ise direkt kullan
if "shape" in df.columns:
    xyz_shapes = df["shape"].astype(str).tolist()
# 2) Alternatif: ayrı sütunlar varsa (örn. x, y, z) her satırı "x,y,z x,y,z ..." yap
elif {"x", "y", "z", "group_id"}.issubset(df.columns):
    # group_id: aynı XML shape'e ait noktaları gruplamak için (varsayım)
    parts = []
    for _, g in df.groupby("group_id"):
        parts.append(" ".join(f"{x},{y},{z}" for x, y, z in zip(g["x"], g["y"], g["z"])))
    xyz_shapes = parts
else:
    raise ValueError("DataFrame içinde beklenen 'shape' ya da (x,y,z,+group_id) kolonları yok.")

# XML'i yükle
tree = ET.parse("eskisehir_last.net.xml")
root = tree.getroot()

# XML içindeki shape attribute'lu elemanları sırayla topla
shape_elems = [elem for elem in root.iter() if "shape" in elem.attrib]

# Uzunluk kontrolü
if len(shape_elems) != len(xyz_shapes):
    print(f"Uyarı: XML'de {len(shape_elems)} shape var ama DataFrame'de {len(xyz_shapes)} satır var.")
    # Yine de minimum ortak uzunluk kadar yazalım:
    n = min(len(shape_elems), len(xyz_shapes))
    for elem, shp in zip(shape_elems[:n], xyz_shapes[:n]):
        elem.set("shape", shp)
else:
    for elem, shp in zip(shape_elems, xyz_shapes):
        elem.set("shape", shp)

# Yeni dosyaya yaz
tree.write("eskisehir_last_with_z.net.xml", encoding="utf-8", xml_declaration=True)

