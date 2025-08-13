import rasterio
from pyproj import Transformer
import numpy as np

def get_elevation(lat, lon, file_path='config/output_hh.tif'):
    # GeoTIFF dosyasını aç
    with rasterio.open(file_path) as dataset:
        data = dataset.read(1)
        height, width = data.shape

        # Noktayı raster CRS'ine dönüştür
        to_raster = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
        x, y = to_raster.transform(lon, lat)

        # Piksel indeksini bul
        row, col = dataset.index(x, y)

        # Piksel kapsam kontrolü
        if not (0 <= row < height and 0 <= col < width):
            return 0  # Raster dışında

        elevation_value = data[row, col]

        # NoData kontrolü
        nodata = dataset.nodata
        if nodata is not None and np.isfinite(nodata) and elevation_value == nodata:
            return None  # Veri yok
        return elevation_value