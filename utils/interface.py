import tkinter as tk
from tkinter import messagebox
import subprocess
import pandas as pd
import joblib


def hesapla_gercek_ve_tahmin(target_vehicle_id):
    """
    target_vehicle_id: 'veh103' gibi bir araç ID'si
    return_all=False  : (total_true, total_pred) döndürür
    return_all=True   : (total_true, total_pred, diff, diff_pct) döndürür
    print_output=True : Sonuçları konsola basar
    """
    csv_path = "data/final_training_data.csv"
    df = pd.read_csv(csv_path)

    # slope_pct sınırları → ±50% üstü/altı fiziksel olarak anlamlı değil
    df = df[(df["slope_pct"] < 50) & (df["slope_pct"] > -50)]
    # 3. Eksik slope_pct → 0 (eğim verisi yoksa "düz" kabul edilir)
    df["slope_pct"] = df["slope_pct"].fillna(0)
    # 'dist_m' sütunundaki NaN değerleri 0 ile doldurur
    df['dist_m'] = df['dist_m'].fillna(0)

    # ivme ayrımı
    # bu sayede enerji tüketimi (hızlanırken) ve rejeneratif enerji kazanımı (yavaşlarken) ayrı ayrı analiz edilebilir.
    # verimlilik hesaplarını ve optimizasyonu daha doğru yapmayı sağlar
    # Pozitif ivme (gaz) tüketimi artırır; negatif ivme (fren/iniş) rejenerasyon sağlayabilir. Tek sütun olsa bu fark kaybolabilirdi
    df["acc_pos"] = df["acceleration"].clip(lower=0)
    df["acc_neg"] = (-df["acceleration"]).clip(lower=0)

    # eğim de ivme gibi negatif ve pozitif şeklinde ayrılmalı
    df["slope_pct_pos"] = df["slope_pct"].clip(lower=0)
    df["slope_pct_neg"] = (-df["slope_pct"]).clip(lower=0)

    # Hız: m/s ve v^2
    df["speed_ms"] = df["speed_kmh"] / 3.6
    df["v2"] = df["speed_ms"] ** 2 # Hızın kareli hali (kinetik enerjiyle ilişkili) modeller için anlamlı yeni bir değişkendir

# Aerodinamik: Cd * A
    df["CdA"] = df["airDragCoefficient"] * df["frontSurfaceArea"] # bu ikini birleştirip vermek daha mantıklı

    # Sadece bu araca ait satırlar
    mask = df["vehicle_id"] == target_vehicle_id

    if not mask.any():
        raise ValueError(f"{target_vehicle_id} için test setinde uygun satır bulunamadı.")

    feature_cols = [
    "v2",                      # hızın karesi (kinetik enerji ile ilişkili)
    "acc_pos", "acc_neg",       # hızlanma / frenleme ,  enerji tüketimi & rejenerasyon
    "slope_pct_pos", "slope_pct_neg",  # eğim pozitif/negatif
    "mass_kg", "CdA", "rollDragCoefficient",   # araç fiziği
    "propulsionEfficiency", "recuperationEfficiency",  # # enerji verimliliği
    "maximumPower"      # motorun max gücü
    ]
    # Hedef ve kimlik dışındaki sütunları özellik olarak kullan
    X_vehicle = df.loc[mask, feature_cols].dropna()

    if X_vehicle.empty:
        raise ValueError(f"{target_vehicle_id} için özellikler NaN sonrası boş kaldı (eksik veri).")

    y_true_vehicle = df.loc[X_vehicle.index, "energy_consumption"]

    # Modeli yükle (pickle dosyası pandas ile de okunabilir)
    rf_path = "data/rf_energy_sumo_ev_model.pkl"
    rf_final = joblib.load(rf_path)

    # Tahmin
    y_pred_vehicle = rf_final.predict(X_vehicle)

    # Toplamlar
    total_true = float(y_true_vehicle.sum())
    total_pred = float(y_pred_vehicle.sum())

    return total_true, total_pred


def run_sumo():
    try:
        subprocess.Popen(["sumo-gui", "-c", "config/main.sumocfg"])
    except FileNotFoundError:
        messagebox.showerror("Hata", "sumo-gui bulunamadı. PATH ayarlarını kontrol et.")
    except Exception as e:
        messagebox.showerror("Hata", f"SUMO başlatılırken hata oluştu:\n{e}")

def validate_num(proposed: str) -> bool:
    # Entry içinde sadece 1-300 arası sayıya izin ver
    if proposed == "":
        return True
    if proposed.isdigit():
        val = int(proposed)
        return 1 <= val <= 300
    return False

def get_vehicle_id_from_input() -> str:
    text = vehicle_num_var.get().strip()
    if not text:
        raise ValueError("Araç numarası boş olamaz.")
    if not text.isdigit():
        raise ValueError("Lütfen sadece sayı girin (1-300).")
    num = int(text)
    if not (1 <= num <= 300):
        raise ValueError("Araç numarası 1 ile 300 arasında olmalı.")
    return f"veh{num}"

def run_hesapla():
    try:
        veh_id = get_vehicle_id_from_input()  # "veh123" gibi
        gercek_toplam, tahmin_toplam = hesapla_gercek_ve_tahmin(veh_id)
        real_var.set(f"{gercek_toplam:.2f} Wh")
        pred_var.set(f"{tahmin_toplam:.2f} Wh")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{e}")

# --- TK arayüz ---
root = tk.Tk()
root.title("Araç Seçimi, Hesaplama ve SUMO")

# Araç numarası girişi
top = tk.Frame(root)
top.pack(padx=12, pady=12, fill="x")

tk.Label(top, text="Araç No (1-300):").pack(side="left")

vehicle_num_var = tk.StringVar()
vcmd = (root.register(validate_num), "%P")
vehicle_num_entry = tk.Entry(top, textvariable=vehicle_num_var, validate="key", validatecommand=vcmd, width=8)
vehicle_num_entry.pack(side="left", padx=8)
vehicle_num_entry.focus_set()

# Çıktılar
out = tk.Frame(root)
out.pack(padx=12, pady=(0, 10), fill="x")

real_var = tk.StringVar(value="—")
pred_var = tk.StringVar(value="—")

row1 = tk.Frame(out); row1.pack(anchor="w", pady=4, fill="x")
tk.Label(row1, text="Gerçek Çıktı:", width=15, anchor="w").pack(side="left")
tk.Entry(row1, textvariable=real_var, state="readonly", width=30).pack(side="left")

row2 = tk.Frame(out); row2.pack(anchor="w", pady=4, fill="x")
tk.Label(row2, text="Tahmin Çıktı:", width=15, anchor="w").pack(side="left")
tk.Entry(row2, textvariable=pred_var, state="readonly", width=30).pack(side="left")

# Butonlar
btns = tk.Frame(root)
btns.pack(padx=12, pady=10, fill="x")

tk.Button(btns, text="Hesapla", command=run_hesapla).pack(side="left", padx=(0,8))
tk.Button(btns, text="SUMO'yu Başlat", command=run_sumo).pack(side="left")

root.mainloop()
