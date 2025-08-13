import rasterio
from rasterio.warp import transform_bounds
from pyproj import Transformer
import matplotlib.pyplot as plt
import numpy as np

# GeoTIFF dosyasını aç
file_path = 'config/output_hh.tif'
dataset = rasterio.open(file_path)

# Veriyi oku (1. bant)
data = dataset.read(1)
height, width = data.shape

# Raster sınırları (raster CRS'inde)
left, bottom, right, top = dataset.bounds

# Sorgu noktası (WGS84: lon/lat)
latitude = 39.75841646363799
longitude = 30.505696566937953

# Noktayı raster CRS'ine dönüştür (EPSG:4326 -> dataset.crs)
# always_xy=True: (lon, lat) sırası garanti
to_raster = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
x, y = to_raster.transform(longitude, latitude)

# Piksel indeksini bul
row, col = dataset.index(x, y)

# Piksel dizinleri geçerli mi?
if not (0 <= row < height and 0 <= col < width):
    # Bilgilendirme için raster sınırlarını WGS84'e çevirip yazdır
    try:
        wgs_bounds = transform_bounds(dataset.crs, "EPSG:4326",
                                      left, bottom, right, top, densify_pts=21)
        minlon, minlat, maxlon, maxlat = wgs_bounds
        print("Uyarı: Nokta raster kapsamı dışında.")
        print(f"Raster WGS84 kapsaması: lon [{minlon:.6f}, {maxlon:.6f}], "
              f"lat [{minlat:.6f}, {maxlat:.6f}]")
        print(f"Sorgu noktası: lon {longitude}, lat {latitude}")
    except Exception:
        print("Uyarı: Nokta raster kapsamı dışında ve WGS84 sınırlar hesaplanamadı.")
    # İsterseniz en yakın pikselden değer okumak için şu satırları açabilirsiniz:
    # row_clamped = int(np.clip(row, 0, height - 1))
    # col_clamped = int(np.clip(col, 0, width - 1))
    # elevation_value = data[row_clamped, col_clamped]
    # print(f"En yakın pikselde (row={row_clamped}, col={col_clamped}) yükseklik: {elevation_value}")
else:
    elevation_value = data[row, col]
    # NoData kontrolü
    nodata = dataset.nodata
    if nodata is not None and np.isfinite(nodata) and elevation_value == nodata:
        print(f"Koordinat (lat={latitude}, lon={longitude}) için piksel NoData içeriyor ({nodata}).")
    else:
        print(f"Koordinat (lat={latitude}, lon={longitude}) için yükseklik: {elevation_value}")

# (Opsiyonel) Görselleştirme — raster CRS'inde extent ile
plt.figure(figsize=(8, 8))
plt.imshow(data, extent=[left, right, bottom, top], cmap='terrain', origin='upper')
plt.colorbar(label='Elevation')

# Noktayı raster CRS'ine dönüştürdüğümüz x,y ile işaretle
plt.scatter([x], [y], s=100, facecolors='none', edgecolors='red', linewidths=2)
plt.title('GeoTIFF Görselleştirmesi (Raster CRS)')
plt.xlabel(f'X ({dataset.crs})')
plt.ylabel(f'Y ({dataset.crs})')
plt.tight_layout()
plt.show()
