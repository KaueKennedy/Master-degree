import pandapower.converter as pc
import matplotlib.pyplot as plt
import pandas as pd

# Caminho do arquivo MATPOWER
mpc_file = "case_texas2k_series25.m"

# Converter MATPOWER -> pandapower network
net = pc.from_mpc(mpc_file)

# Verificar as primeiras colunas do DataFrame de barramentos
print(net.bus.head())

# Se o arquivo tiver colunas 'lat' e 'lon', ótimo
if "lat" in net.bus.columns and "lon" in net.bus.columns:
    lat = net.bus["lat"]
    lon = net.bus["lon"]
else:
    # fallback: alguns casos usam 'x' e 'y' para coordenadas
    lat = net.bus["y"]
    lon = net.bus["x"]

# Plot simples dos barramentos
plt.figure(figsize=(10,8))
plt.scatter(lon, lat, c="red", s=5)
plt.title("Mapa - Texas2k Series25 (Barramentos)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()
