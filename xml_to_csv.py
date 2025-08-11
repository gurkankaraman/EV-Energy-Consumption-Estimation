import xml.etree.ElementTree as ET
import pandas as pd

# 1. fcd-export XML'den tüm vehicle attribute'larını oku
def parse_fcd_export(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    for timestep in root.findall('timestep'):
        time = timestep.attrib.get('time')
        for vehicle in timestep.findall('vehicle'):
            # Tüm attribute'ları alıyoruz, time'ı ayrıca ekle
            row = {k: v for k, v in vehicle.attrib.items()}
            row['time'] = float(time)
            # numeric olanları float yapmaya çalışalım
            for key in ['x','y','z','angle','speed','pos','slope']:
                if key in row:
                    try:
                        row[key] = float(row[key])
                    except:
                        pass
            data.append(row)
    return pd.DataFrame(data)

# 2. vTypes XML'den vType attribute ve param key-value çifti olarak oku
def parse_vtypes(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    for vtype in root.findall('vType'):
        row = {k: vtype.attrib.get(k) for k in vtype.attrib.keys()}
        # Numeric dönüşümler
        for key in ['accel','decel','length','maxSpeed','sigma','minGap','mass']:
            if key in row:
                try:
                    row[key] = float(row[key])
                except:
                    pass
        # param taglerini de key-value olarak ekle
        for param in vtype.findall('param'):
            key = param.attrib.get('key')
            value = param.attrib.get('value')
            if key:
                # numeric ise float yap
                try:
                    value = float(value)
                except:
                    pass
                row[key] = value
        data.append(row)
    return pd.DataFrame(data)

# 3. emission-export XML'den tüm vehicle attribute'larını oku
def parse_emission_export(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    data = []
    for timestep in root.findall('timestep'):
        time = timestep.attrib.get('time')
        for vehicle in timestep.findall('vehicle'):
            row = {k: v for k, v in vehicle.attrib.items()}
            row['time'] = float(time)
            # numeric dönüşüm yapmaya çalış
            for key in ['CO2','NOx','PMx','fuel','electricity','noise','speed','x','y','z','angle','pos','waiting','lane']:
                if key in row:
                    try:
                        row[key] = float(row[key])
                    except:
                        pass
            data.append(row)
    return pd.DataFrame(data)

# Dosya yolları
fcd_path = "fcd_output.xml"
vtypes_path = "vehicles.add.xml"
emission_path = "emission_output.xml"

# XML'den oku
df_fcd = parse_fcd_export(fcd_path)
df_vtypes = parse_vtypes(vtypes_path)
df_emission = parse_emission_export(emission_path)

# Merge: fcd ve emission 'id', 'time' ve 'type' ile birleştir
df_merged = pd.merge(df_fcd, df_emission, on=['id', 'time', 'type'], suffixes=('_fcd', '_emission'), how='outer')

# vTypes ile 'type' ve 'id' eşleşerek birleştir
df_final = pd.merge(df_merged, df_vtypes, left_on='type', right_on='id', how='left')

# Gereksiz sütunları at (örneğin vTypes'deki id)
df_final = df_final.drop(columns=['id_y'])  # 'id_y' vTypes'den gelen id
df_final = df_final.rename(columns={'id_x':'id'})  # ana id sütununu düzelt

# CSV olarak kaydet
df_final.to_csv('combined_data2.csv', index=False)

print("CSV dosyası oluşturuldu: combined_data.csv")
