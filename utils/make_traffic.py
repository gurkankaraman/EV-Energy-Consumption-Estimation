import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import sumolib  # Comes with SUMO; if missing: pip install sumolib

# --- SETTINGS ---
input_xml = "config/eskisehir_last_with_z.net.xml"   # SUMO network file containing edges
output_rou = "config/random_routes.rou.xml"                  # output routes file
num_vehicles = 300                                  # number of vehicles to generate
max_attempts_multiplier = 50                          # limit for path search attempts (= num_vehicles * multiplier)

# 1) Extract residential edge IDs from the network XML
tree = ET.parse(input_xml)
root = tree.getroot()

residential_ids = [
    edge.get("id")
    for edge in root.findall(".//edge")
    if edge.get("type") == "highway.residential"
]

if len(residential_ids) < 2:
    raise ValueError("Need at least 2 'highway.residential' edges to select random start/end edges.")

# 1b) Load the network with sumolib for path calculation
net = sumolib.net.readNet(input_xml)

def route_edges_between_and_extend(edge_from_id, edge_to_id, steps=10, attempts_per_step=20):
    """
    edge_from_id -> edge_to_id için en kısa yolu bulur, ardından e_to'dan başlayıp
    rastgele hedeflere doğru 'steps' kez daha uzatır.
    Yol parçalarını birleştirir ve edge ID'lerinin listesini döndürür.
    Her adımda yol bulunamazsa birkaç kez (attempts_per_step) başka hedefler dener.
    Hiç yol bulunamazsa o ana kadarki birikmiş yol döndürülür; başlangıçta hiç yol yoksa None döner.
    """
    try:
        e_from = net.getEdge(edge_from_id)
        e_to   = net.getEdge(edge_to_id)
    except Exception:
        return None

    # İlk parça: e_from -> e_to
    path, _ = net.getShortestPath(e_from, e_to)  # Dijkstra
    if not path:
        return None

    full_ids = [e.getID() for e in path]
    current_edge = e_to

    # Rastgele seçimler için hazır liste
    try:
        all_edges = list(net.getEdges())
    except Exception:
        # Bazı API'lerde getEdges yerine getEdgeIDs kullanılabilir
        all_edges = [net.getEdge(eid) for eid in net.getEdgeIDs()]

    # 'steps' kez daha yol ekle
    for _ in range(steps):
        extended = False

        # Yol çıkmayan hedeflere takılmamak için birkaç deneme yap
        for _try in range(attempts_per_step):
            cand = random.choice(all_edges)
            if cand.getID() == current_edge.getID():
                continue

            seg, _ = net.getShortestPath(current_edge, cand)
            if not seg:
                continue

            # Segmenti ekle (bağlantı kenarı tekrarını önlemek için ilk kenarı atla)
            seg_ids = [e.getID() for e in seg]
            if full_ids and seg_ids and full_ids[-1] == seg_ids[0]:
                seg_ids = seg_ids[1:]

            full_ids.extend(seg_ids)
            current_edge = cand
            extended = True
            break

        if not extended:
            # Bu adımda hiç yol bulunamadı; uzatmayı erken kes.
            break

    return full_ids

# 2) Create the root <routes> element
routes_root = ET.Element("routes")

# 3) Generate vehicles: pick two residential edges and find the connecting path
created = 0
attempts = 0
max_attempts = num_vehicles * max_attempts_multiplier

while created < num_vehicles and attempts < max_attempts:
    attempts += 1
    a, b = random.sample(residential_ids, 2)
    path_edges = route_edges_between_and_extend(a, b)
    if not path_edges:
        continue  # No connection; try another pair

    electric_type = random.randint(1, 20)  # Randomly select an electric vehicle type
    veh_id = f"veh{created + 1}"
    vehicle_el = ET.SubElement(
        routes_root, "vehicle",
        id=veh_id,
        depart=str(float(created + 1)),
        type=f"electric{electric_type}"
    )

    battery_charge_level_value = electric_type * 4000 + random.randint(10000, 20000)
    ET.SubElement(
        vehicle_el, "param",
        key="device.battery.chargeLevel",
        value=str(battery_charge_level_value)
    )

    ET.SubElement(vehicle_el, "route", edges=" ".join(path_edges))
    created += 1

if created < num_vehicles:
    print(f"Warning: Only {created} out of {num_vehicles} vehicles could be generated. "
          f"(attempts: {attempts}/{max_attempts})")

# 4) Pretty-print and save to file
rough_xml = ET.tostring(routes_root, encoding="utf-8")
pretty_xml = minidom.parseString(rough_xml).toprettyxml(indent="  ")

with open(output_rou, "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print(f"{output_rou} created. Vehicles generated: {created} (target: {num_vehicles}, attempts: {attempts})")
