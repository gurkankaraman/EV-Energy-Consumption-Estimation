import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import rowcol
from pyproj import CRS, Transformer
import math

# ---------- PATHS ----------
NET_XML_PATH = "eskisehir.net.xml"
RASTER_PATH  = "eskisehir.tif"
OUT_XML_PATH = "eskisehir_height3d_edges_only.net.xml"

# ---------- SAMPLING (küçük dosya için düşük tut) ----------
EDGE_SAMPLES_PER_100M = 3
MIN_SAMPLES = 3

# ---------- HELPERS ----------
def polyline_length(points_xy):
    if len(points_xy) < 2:
        return 0.0
    return sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(points_xy[:-1], points_xy[1:]))

def resample_polyline(points_xy, desired_count):
    if not points_xy:
        return []
    if len(points_xy) == 1:
        return [points_xy[0]] * desired_count

    seg_lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(points_xy[:-1], points_xy[1:])]
    total_len = sum(seg_lengths)
    if total_len == 0:
        return [points_xy[0]] * desired_count

    targets = np.linspace(0.0, total_len, desired_count)
    out = []
    acc = 0.0; seg_idx = 0
    p0 = points_xy[0]; p1 = points_xy[1]
    seg_len = seg_lengths[0]; traveled = 0.0

    def interp(pa, pb, t):
        return (pa[0] + (pb[0]-pa[0]) * t, pa[1] + (pb[1]-pa[1]) * t)

    for tdist in targets:
        while seg_idx < len(seg_lengths)-1 and acc + (seg_len - traveled) < tdist:
            acc += (seg_len - traveled)
            seg_idx += 1
            p0 = points_xy[seg_idx]; p1 = points_xy[seg_idx+1]
            seg_len = seg_lengths[seg_idx]; traveled = 0.0
        remain = tdist - acc
        frac = 0.0 if seg_len == 0 else (traveled + remain) / seg_len
        frac = max(0.0, min(1.0, frac))
        out.append(interp(p0, p1, frac))
        traveled += remain
    return out

def parse_shape(shape_str):
    pts = []
    for tok in shape_str.strip().split():
        parts = tok.split(",")
        if len(parts) >= 2:
            pts.append((float(parts[0]), float(parts[1])))
    return pts

def format_shape_xyz(points_xy, zs):
    # z bulunamazsa 0.0 yazıyoruz (SUMO 3B görüntü için)
    return " ".join(f"{x:.3f},{y:.3f},{(z if z is not None else 0.0):.3f}"
                    for (x, y), z in zip(points_xy, zs))

# ---------- MAIN ----------
def main():
    root = ET.parse(NET_XML_PATH).getroot()
    loc = root.find("location")

    # Ağ bilgileri
    net_offset = (0.0, 0.0)
    if loc is not None and loc.get("netOffset"):
        ox, oy = loc.get("netOffset").split(",")
        net_offset = (float(ox), float(oy))

    proj4 = loc.get("projParameter") if loc is not None else None

    with rasterio.open(RASTER_PATH) as ds:
        raster_crs = ds.crs                # EPSG:4326 (GeoTIFF)
        utm_crs = CRS.from_proj4(proj4)    # UTM Zone 36 (net.xml)
        to_raster_crs = Transformer.from_crs(utm_crs, raster_crs, always_xy=True)

        band = ds.read(1, masked=True)
        H, W = band.shape
        has_mask = hasattr(band, "mask") and getattr(band.mask, "shape", None) == band.shape

        def sample_z(x_local, y_local):
            # DOĞRU DÖNÜŞÜM: UTM = local - netOffset, ardından UTM -> raster CRS
            Xutm = x_local - net_offset[0]
            Yutm = y_local - net_offset[1]
            Xr, Yr = to_raster_crs.transform(Xutm, Yutm)
            r, c = rowcol(ds.transform, Xr, Yr, op=round)
            if 0 <= r < H and 0 <= c < W and not (has_mask and band.mask[r, c]):
                return float(band[r, c])
            return None

        # 1) Junction'lara z yaz
        for j in root.findall("junction"):
            try:
                x = float(j.get("x")); y = float(j.get("y"))
            except Exception:
                continue
            z = sample_z(x, y)
            if z is not None:
                j.set("z", f"{z:.3f}")

        # 2) Edge shape'larını 3B yap
        for e in root.findall("edge"):
            if e.get("function") == "internal":
                continue
            shape = e.get("shape")
            if shape:
                pts = parse_shape(shape)
                L = polyline_length(pts)
                n = max(MIN_SAMPLES, int((L / 100.0) * EDGE_SAMPLES_PER_100M))
                dense_xy = resample_polyline(pts, n)
                zs = [sample_z(x, y) for (x, y) in dense_xy]
                e.set("shape", format_shape_xyz(dense_xy, zs))
            else:
                # shape yoksa from/to junctionlardan en az 2 noktalı 3B shape kur
                fid, tid = e.get("from"), e.get("to")
                jf = root.find(f"junction[@id='{fid}']")
                jt = root.find(f"junction[@id='{tid}']")
                if jf is not None and jt is not None:
                    xf, yf = float(jf.get("x")), float(jf.get("y"))
                    xt, yt = float(jt.get("x")), float(jt.get("y"))
                    zf = sample_z(xf, yf)
                    zt = sample_z(xt, yt)
                    e.set("shape", format_shape_xyz([(xf, yf), (xt, yt)], [zf, zt]))

    # Kaydet
    Path(OUT_XML_PATH).write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    print(f"Written: {OUT_XML_PATH}")

if __name__ == "__main__":
    main()
