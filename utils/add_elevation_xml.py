# Streaming olarak XML içindeki shape="..." değerlerine z=0.0 ekleyip
# yapıyı bozmadan (satır sırasını ve diğer içerikleri koruyarak) yeni dosyaya yazalım.

import re
import get_elevation
import calculate_lan_lot

input_path = "config/eskisehir.net.xml"
output_path = "config/eskisehir_last_with_z.net.xml"

# shape="..."
shape_attr_start = 'shape="'

def add_z_to_shape_text(shape_text):
    # shape_text: "x,y x,y x,y"
    tokens = shape_text.strip().split()
    out_tokens = []
    for t in tokens:
        parts = t.split(",")
        if len(parts) == 2:
            x, y = parts
            lat, lon = calculate_lan_lot.local_to_latlon(float(x), float(y))
            z = get_elevation.get_elevation(lat, lon)
            out_tokens.append(f"{x},{y},{z}")
        elif len(parts) == 3:
            # Zaten z var -> dokunma
            out_tokens.append(t)
        else:
            # Beklenmeyen durum -> olduğu gibi bırak
            out_tokens.append(t)
    return " ".join(out_tokens)

with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
    buffering_shape = False
    buffer_before = ""   # shape=" öncesi
    buffer_shape = ""    # shape içeriği
    buffer_after = ""    # shape kapanışından sonrası

    while True:
        line = fin.readline()
        if not line:
            # Dosya bitti; eğer hala buffer varsa yaz
            if buffering_shape:
                # Kapanış tırnağı gelmeden dosya bitti: güvenli olmak için eskiyi yaz
                fout.write(buffer_before + shape_attr_start + buffer_shape)
            break

        if not buffering_shape:
            # Bu satırda shape=" var mı?
            idx = line.find(shape_attr_start)
            if idx == -1:
                # Yoksa direkt yaz
                fout.write(line)
                continue

            # shape=" bulundu -> öncesini yaz, sonrasını işle
            buffering_shape = True
            buffer_before = line[:idx]
            rest = line[idx + len(shape_attr_start):]

            # rest içerisinde kapanış tırnağı var mı?
            end_idx = rest.find('"')
            if end_idx != -1:
                # Aynı satırda bitiyor
                buffer_shape = rest[:end_idx]
                buffer_after = rest[end_idx+1:]  # kapanış tırnağından sonrası

                # Dönüştür
                new_shape = add_z_to_shape_text(buffer_shape)
                # Yaz ve state sıfırla
                fout.write(buffer_before + shape_attr_start + new_shape + '"' + buffer_after)
                buffering_shape = False
                buffer_before = buffer_shape = buffer_after = ""
            else:
                # Birden fazla satıra yayılmış
                buffer_shape = rest
                # Çok satırlı shape değerinde yapı korunacak şekilde buffer'lamaya devam
        else:
            # buffering_shape True -> shape içeriği devam ediyor
            end_idx = line.find('"')
            if end_idx == -1:
                # Hâlâ kapanmadı -> shape verisine ekle ve devam et
                buffer_shape += "\n" + line  # satır sonları korunur
            else:
                # Kapanış burada
                buffer_shape += "\n" + line[:end_idx]
                buffer_after = line[end_idx+1:]

                # Dönüştür (çok satırlı shape içlerinde varsa satır sonlarını korumak için
                # önce satırları bölüp her satırdaki koordinatları dönüştürelim)
                lines = buffer_shape.splitlines()
                new_lines = [add_z_to_shape_text(s, "0.0") for s in lines]
                new_shape = "\n".join(new_lines)

                # Yaz ve state sıfırla
                fout.write(buffer_before + shape_attr_start + new_shape + '"' + buffer_after)
                buffering_shape = False
                buffer_before = buffer_shape = buffer_after = ""

print(f"Z değerleri eklendi: {input_path} -> {output_path}")
