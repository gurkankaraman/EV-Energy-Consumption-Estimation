# live_logger_geo.py
import csv, os, math
import traci

PORT = 8813
OUT = "data_run_live.csv"
STEP = 0.5              # sumo --step-length ile aynı tut
END_TIME = None         # araç bittiğinde çık
MAX_TIME = 100          # kolay takip için kısa, prod'da 1200+ yap

FIELDS = [
    "t","veh_id",
    "lon","lat","z",
    "speed","accel",
    "edge_id","lane_id","lane_pos","angle_deg","lane_speed_limit",
    "grade_pct",
    # battery (dokümantasyon parametreleri)
    "chargeLevel_Wh","capacity_Wh","soc_pct",
    "energyConsumed_Wh","energyCharged_Wh",
    "totalEnergyConsumed_Wh","totalEnergyRegenerated_Wh",
    "maximumChargeRate_W",
]

def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default

def haversine_m(lat1, lon1, lat2, lon2):
    # metre cinsinden Haversine mesafesi
    R = 6371000.0
    if None in (lat1, lon1, lat2, lon2):
        return None
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def compute_grade(prev, cur):
    # grade(%) = 100 * dz / haversine_distance
    (plon, plat, pz, _) = prev
    (lon,  lat,  z,  _) = cur
    if any(v is None or (isinstance(v, float) and v != v) for v in (plon,plat,pz,lon,lat,z)):
        return None
    d_xy = haversine_m(plat, plon, lat, lon)
    if not d_xy or d_xy <= 0:
        return None
    return 100.0 * (z - pz) / d_xy

def get_vehicle_info(conn, vid, prev_state, step_len):
    # ağ koordinatı -> geo (lon,lat)
    x, y = safe(lambda: conn.vehicle.getPosition(vid), (None, None))
    lon, lat = (None, None)
    if x is not None and y is not None:
        lon, lat = safe(lambda: conn.simulation.convertGeo(x, y), (None, None))

    # 3B yükseklik
    z = safe(lambda: conn.vehicle.getPosition3D(vid), (None, None, None))[2]

    # hız / ivme / eğim
    speed = safe(lambda: conn.vehicle.getSpeed(vid), None)
    accel = None
    grade = None
    if vid in prev_state and step_len and speed is not None and prev_state[vid][3] is not None:
        accel = (speed - prev_state[vid][3]) / step_len
        grade = compute_grade(prev_state[vid], (lon, lat, z, speed))
    prev_state[vid] = (lon, lat, z, speed)

    # yol/şerit
    edge_id   = safe(lambda: conn.vehicle.getRoadID(vid), "")
    lane_id   = safe(lambda: conn.vehicle.getLaneID(vid), "")
    lane_pos  = safe(lambda: conn.vehicle.getLanePosition(vid), None)
    angle_deg = safe(lambda: conn.vehicle.getAngle(vid), None)
    lane_vmax = safe(lambda: conn.lane.getMaxSpeed(lane_id), None) if lane_id else None

    # Battery — sadece SUMO dokümantasyonundaki anahtarlar
    chargeLevel = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.chargeLevel"))
    capacity    = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.capacity"))
    energyCons  = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.energyConsumed"))
    energyChg   = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.energyCharged"))
    totalCons   = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.totalEnergyConsumed"))
    totalRegen  = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.totalEnergyRegenerated"))
    maxRate     = safe(lambda: conn.vehicle.getParameter(vid, "device.battery.maximumChargeRate"))

    # SOC = chargeLevel / capacity
    soc_pct = None
    try:
        if chargeLevel is not None and capacity not in (None, "0", 0, 0.0):
            soc_pct = 100.0 * (float(chargeLevel) / float(capacity))
    except Exception:
        soc_pct = None

    return {
        "lon": lon, "lat": lat, "z": z,
        "speed": speed, "accel": accel,
        "edge_id": edge_id, "lane_id": lane_id, "lane_pos": lane_pos,
        "angle_deg": angle_deg, "lane_speed_limit": lane_vmax,
        "grade_pct": grade,
        "chargeLevel_Wh": chargeLevel, "capacity_Wh": capacity, "soc_pct": soc_pct,
        "energyConsumed_Wh": energyCons, "energyCharged_Wh": energyChg,
        "totalEnergyConsumed_Wh": totalCons, "totalEnergyRegenerated_Wh": totalRegen,
        "maximumChargeRate_W": maxRate,
    }, prev_state

def main():
    print(f"[info] bağlanılıyor port={PORT} ...")
    conn = traci.connect(port=PORT)
    print("[info] bağlı. yazılacak dosya:", os.path.abspath(OUT))

    new_file = not os.path.exists(OUT)
    f = open(OUT, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new_file:
        w.writeheader(); f.flush()

    prev_state = {}
    last_log_t = -1.0

    try:
        while True:
            conn.simulationStep()
            t = conn.simulation.getTime()

            if int(t) != int(last_log_t):
                print(f"[step] t={t:.1f}s veh={len(conn.vehicle.getIDList())}")
                last_log_t = t

            for vid in conn.vehicle.getIDList():
                info, prev_state = get_vehicle_info(conn, vid, prev_state, STEP)
                w.writerow({"t": t, "veh_id": vid, **info})
                f.flush()

            # çıkış koşulları
            if END_TIME is None:
                if t >= MAX_TIME:
                    print("[info] MAX_TIME doldu, çıkılıyor."); break
                if t > 0 and conn.simulation.getMinExpectedNumber() == 0:
                    print("[info] Araç kalmadı, çıkılıyor."); break
            else:
                if t >= END_TIME:
                    print("[info] END_TIME'ye ulaşıldı, çıkılıyor."); break

    finally:
        try: conn.close(False)
        except: pass
        f.close(); print("[info] kapatıldı.")

if __name__ == "__main__":
    main()
