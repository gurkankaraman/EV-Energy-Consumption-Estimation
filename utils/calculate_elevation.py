import xml.etree.ElementTree as ET
import pandas as pd
import calculate_lan_lot
import calculate_z
import time

def extract_shapes_with_z_first_point(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    shapes = []
    shape_index = 0
    calls_in_minute = 0
    start_time = time.time()

    for elem in root.iter():
        if 'shape' in elem.attrib:
            shape_index += 1
            shape_str = elem.attrib['shape'].strip()
            if not shape_str:
                continue

            coords = shape_str.split()

            try:
                first_x_str, first_y_str = coords[0].split(",")
                first_x = float(first_x_str)
                first_y = float(first_y_str)

                # Rate limit kontrolü
                if calls_in_minute >= 80:
                    elapsed = time.time() - start_time
                    if elapsed < 60:
                        wait_time = 60 - elapsed
                        print(f"⚠ 80 API çağrısı limitine ulaşıldı, {wait_time:.2f} sn bekleniyor...")
                        time.sleep(wait_time)
                    start_time = time.time()
                    calls_in_minute = 0

                # yerel -> lat/lon
                lon, lat = calculate_lan_lot.local_to_latlon(first_x, first_y)

                # API çağrısı
                z_val = calculate_z.get_elevation(lat, lon)
                calls_in_minute += 1

                if isinstance(z_val, (list, tuple)):
                    z_val = z_val[0]

                z = float(z_val)
            except Exception as e:
                z = 0.0
                print(f"[shape {shape_index}] z hesaplanırken hata: {e}; z=0 atanıyor.")

            new_coords = []
            for pair in coords:
                try:
                    x_str, y_str = pair.split(",")
                    new_coords.append(f"{x_str},{y_str},{z}")
                except ValueError:
                    continue

            shapes.append(" ".join(new_coords))

            with open("log.txt", "a", encoding="utf-8") as dosya:
                if z != 0.0:
                    print(f"[shape {shape_index}] done: z={z}")
                    dosya.write(f"[shape {shape_index}] done: z={z}\n")
                else:
                    print(f"[shape {shape_index}] error: z=0")
                    dosya.write(f"[shape {shape_index}] error: z=0\n")

    df_shapes = pd.DataFrame(shapes, columns=["shape"])
    return df_shapes