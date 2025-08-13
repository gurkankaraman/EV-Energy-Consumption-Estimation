import get_elevation
import calculate_lan_lot

x = 1283.69
y = 1357.31

lat, lon = calculate_lan_lot.local_to_latlon(x, y)

z = get_elevation.get_elevation(lat, lon)   

print(round(z, 2))  # Z değerini iki ondalık basamakla yazdır