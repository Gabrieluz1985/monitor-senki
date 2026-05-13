import requests
import re
import pandas as pd
import os

# ===================================
# MARCAS A MONITOREAR
# ===================================

MARCAS = [
    "ADAK",
    "PIONEER",
    "USINA",
    "STETSOM",
    "TRITON",
    "SPYDER",
    "HINOR",
    "CONO",
    "AJK"
]

# ===================================
# TELEGRAM
# ===================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "6519393068"

# ===================================
# URL SENKI
# ===================================

URL = "https://www.senkielectronica.com/lista-de-precos"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

html = response.text

print("Status:", response.status_code)

# ===================================
# EXTRAER PRODUCTOS
# ===================================

padrao = r'(\d{4,})\s+(.+?)\s+U\$(\d+,\d+)'

resultados = re.findall(padrao, html)

productos = []

for codigo, nombre, precio in resultados:

    codigo = str(codigo).strip()

    nombre = " ".join(nombre.split())

    precio_float = float(precio.replace(",", "."))

    productos.append({
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio_float
    })

df_actual = pd.DataFrame(productos)

print(f"\nProductos encontrados: {len(df_actual)}")

archivo_anterior = "productos_anterior.csv"

# ===================================
# TELEGRAM
# ===================================

def enviar_telegram(mensaje):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    requests.post(url, data=data)

# ===================================
# PRIMERA EJECUCIÓN
# ===================================

if not os.path.exists(archivo_anterior):

    df_actual.to_csv(archivo_anterior, index=False, encoding="utf-8-sig")

    print("\nPrimera ejecución.")
    print("Base guardada correctamente.")

else:

    df_anterior = pd.read_csv(
        archivo_anterior,
        dtype={"codigo": str}
    )

    cambios = []

    anteriores = df_anterior.set_index("codigo").to_dict("index")
    actuales = df_actual.set_index("codigo").to_dict("index")

    # ===================================
    # CAMBIOS Y NUEVOS
    # ===================================

    for codigo, producto_actual in actuales.items():

        nombre_upper = producto_actual["nombre"].upper()

        # SOLO MARCAS FILTRADAS
        if not any(marca in nombre_upper for marca in MARCAS):
            continue

        # PRODUCTO EXISTENTE
        if codigo in anteriores:

            precio_viejo = float(anteriores[codigo]["precio"])
            precio_nuevo = float(producto_actual["precio"])

            if precio_viejo != precio_nuevo:

                diferencia = round(precio_nuevo - precio_viejo, 2)

                emoji = "📈" if diferencia > 0 else "📉"

                cambios.append(
                    f"{emoji} CAMBIO\n\n"
                    f"Producto:\n{producto_actual['nombre']}\n\n"
                    f"Antes: U${precio_viejo}\n"
                    f"Ahora: U${precio_nuevo}\n"
                    f"Diferencia: U${diferencia}\n"
                )

        # PRODUCTO NUEVO
        else:

            cambios.append(
                f"🆕 NUEVO PRODUCTO\n\n"
                f"{producto_actual['nombre']}\n"
                f"Precio: U${producto_actual['precio']}\n"
            )

    # ===================================
    # ELIMINADOS
    # ===================================

    for codigo, producto_anterior in anteriores.items():

        nombre_upper = producto_anterior["nombre"].upper()

        if not any(marca in nombre_upper for marca in MARCAS):
            continue

        if codigo not in actuales:

            cambios.append(
                f"❌ ELIMINADO\n\n"
                f"{producto_anterior['nombre']}"
            )

    # ===================================
    # RESULTADO
    # ===================================

    if cambios:

        print(f"\nCambios detectados: {len(cambios)}")

        mensaje = "⚠️ CAMBIOS EN SENKI ⚠️\n\n"

        mensaje += "\n----------------------\n\n".join(cambios[:15])

        enviar_telegram(mensaje)

        print("Mensaje enviado a Telegram.")

    else:

        print("\nNo hubo cambios.")

    # ===================================
    # ACTUALIZAR BASE
    # ===================================

    df_actual.to_csv(archivo_anterior, index=False, encoding="utf-8-sig")

    print("\nBase actualizada.")
