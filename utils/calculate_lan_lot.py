from pyproj import CRS, Transformer

# CRS tanımları
utm36 = CRS.from_epsg(32636)   # UTM Zone 36N (WGS84)
wgs84 = CRS.from_epsg(4326)    # WGS84 (lat/lon)

# Transformer: UTM → WGS84 (lon, lat)
transformer = Transformer.from_crs(utm36, wgs84, always_xy=True)

# Negatif saklanan ofsetler
NET_OFFSET = (-285155.26, -4402444.03)

def local_to_latlon(x: float, y: float) -> tuple[float, float]:

    # UTM koordinatını hesapla
    utm_e = x - NET_OFFSET[0]
    utm_n = y - NET_OFFSET[1]

    # UTM → WGS84 dönüşümü
    lon, lat = transformer.transform(utm_e, utm_n)

    return lat, lon
