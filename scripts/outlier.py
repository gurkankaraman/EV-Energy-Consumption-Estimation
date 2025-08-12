import pandas as pd

# CSV dosyasını oku
df = pd.read_csv("../data/buyukdere_simulation_data_with_params.csv")

# z sütunu 0 olmayan satırları filtrele
df = df[df["z"] != 0]

# İstenmeyen sütunları kaldır
drop_cols = [
    "vehicle_type", 
    "lane_speed_limit", 
    "vClass", 
    "emissionClass", 
    "sigma", 
    "color", 
    "stoppingThreshold",
    "speed_ms"  # yeni eklenen sütun
]
df = df.drop(columns=drop_cols, errors="ignore")  # eksik sütunlar varsa hata vermesin

# Sonucu tekrar CSV olarak kaydet
df.to_csv("../data/EV_DATA.csv", index=False)

print("Temizlik tamamlandı. '../data/EV_DATA.csv' dosyası oluşturuldu.")

