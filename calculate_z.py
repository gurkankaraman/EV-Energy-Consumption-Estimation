import requests

def get_elevation(lat: float, lon: float, timeout: float = 10.0) -> str:
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        elevation = data.get("elevation", None)
        return elevation if elevation is not None else "0"
    except requests.RequestException:
        return "0"



