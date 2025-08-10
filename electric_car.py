import xml.etree.ElementTree as ET
from xml.dom import minidom

def lerp(a, b, t):
    return a + (b - a) * t

def kmh_to_ms(v_kmh):
    return v_kmh / 3.6

def pretty_xml(elem):
    rough = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="    ")

root = ET.Element("vTypes")

N = 20 # Number of vehicle types
for i in range(1, N + 1):
    t = (i - 1) / (N - 1)  # 0..1

    # Yolcu otomobili parametreleri
    accel = lerp(2.5, 4.0, t)             # m/s^2
    decel = lerp(4.5, 6.0, t)             # m/s^2
    length = lerp(4.0, 5.0, t)            # m
    vmax_kmh = lerp(120.0, 180.0, t)      # km/h
    vmax_ms = kmh_to_ms(vmax_kmh)         # m/s
    minGap = lerp(1.5, 2.0, t)            # m
    mass = int(round(lerp(1200, 2000, t)))# kg

    attrs = {
        "id": f"electric{i}",
        "vClass": "passenger",
        "emissionClass": "Energy/Unknown",
        "accel": f"{accel:.2f}",
        "decel": f"{decel:.2f}",
        "length": f"{length:.2f}",
        "maxSpeed": f"{vmax_ms:.2f}",
        "sigma": "0.0",
        "minGap": f"{minGap:.2f}",
        "mass": f"{mass}",
        "color": "1,1,0",  # Sarı
    }

    vtype = ET.SubElement(root, "vType", attrs)

    # Enerji ve sürtünme parametreleri (binek EV aralıkları)
    params = [
        ("has.battery.device", "true"),
        ("device.battery.capacity", str(int(round(lerp(40000, 100000, t))))),  # Wh
        ("maximumPower", str(int(round(lerp(80000, 200000, t))))),             # W
        ("frontSurfaceArea", f"{lerp(2.0, 2.5, t):.2f}"),                      # m^2
        ("airDragCoefficient", f"{lerp(0.24, 0.35, t):.3f}"),
        ("rotatingMass", str(int(round(lerp(20, 40, t))))),                    # kg eşdeğeri
        ("radialDragCoefficient", f"{lerp(0.40, 0.45, t):.3f}"),
        ("rollDragCoefficient", f"{lerp(0.006, 0.010, t):.3f}"),
        ("constantPowerIntake", str(int(round(lerp(200, 500, t))))),           # W
        ("propulsionEfficiency", f"{lerp(0.85, 0.95, t):.2f}"),
        ("recuperationEfficiency", f"{lerp(0.80, 0.95, t):.2f}"),
        ("stoppingThreshold", "0.1"),
        ("device.battery.maximumChargeRate", str(int(round(lerp(40000, 150000, t))))),  # W
    ]

    for k, v in params:
        p = ET.SubElement(vtype, "param")
        p.set("key", k)
        p.set("value", v)

xml_str = pretty_xml(root)

with open("vehicles.add.xml", "w", encoding="utf-8") as f:
    f.write(xml_str)
