from flask import Flask, render_template, request, jsonify
from collections import deque
import heapq
import math
import csv

app = Flask(__name__)

# ─── Estructuras de datos ───────────────────────────────────────────────────────

class node_trie:
    def __init__(self):
        self.fin = False
        self.hijos = {}


class Trie:
    def __init__(self):
        self.raiz = node_trie()

    def inserta(self, palabra):
        nodo = self.raiz
        for letra in palabra:
            if letra not in nodo.hijos:
                nodo.hijos[letra] = node_trie()
            nodo = nodo.hijos[letra]
        nodo.fin = True

    def autocompletado(self, prefijo):
        nodo = self.raiz
        for letra in prefijo:
            if letra not in nodo.hijos:
                return []
            nodo = nodo.hijos[letra]
        resultados = []
        self._autocompletado_rec(nodo, prefijo, resultados)
        return resultados

    def _autocompletado_rec(self, nodo, palabra_actual, resultados):
        if nodo.fin:
            resultados.append(palabra_actual)
        for letra, siguiente in nodo.hijos.items():
            self._autocompletado_rec(siguiente, palabra_actual + letra, resultados)


class grafos:
    def __init__(self):
        self.G = None

    def prim(self, inicio):
        pi = {}
        llave = {}
        for v in self.G:
            pi[v] = None
            llave[v] = float('inf')
        llave[inicio] = 0
        heap = []
        heapq.heappush(heap, (0, inicio))
        visitado = set()
        while len(heap) > 0:
            peso, v = heapq.heappop(heap)
            if v in visitado:
                continue
            visitado.add(v)
            for k in self.G[v]:
                if k not in visitado and self.G[v][k] < llave[k]:
                    llave[k] = self.G[v][k]
                    pi[k] = v
                    heapq.heappush(heap, (llave[k], k))
        return pi

    def dijkstra(self, inicio):
        pi = {}
        llave = {}
        for v in self.G:
            pi[v] = None
            llave[v] = float('inf')
        llave[inicio] = 0
        heap = []
        heapq.heappush(heap, (0, inicio))
        while len(heap) > 0:
            distancia_actual, u = heapq.heappop(heap)
            for v in self.G[u]:
                if llave[u] + self.G[u][v] < llave[v]:
                    llave[v] = llave[u] + self.G[u][v]
                    pi[v] = u
                    heapq.heappush(heap, (llave[v], v))
        return llave, pi


class Nodo_arbol:
    def __init__(self, punto):
        self.punto = punto
        self.izq = None
        self.der = None


class kd_trees:
    def __init__(self, k):
        self.h = k
        self.raiz = None

    def construir_arbol(self, puntos, profundidad):
        if not puntos:
            return None
        eje = profundidad % self.h
        puntos.sort(key=lambda punto: punto[eje])
        mediana = len(puntos) // 2
        nodo = Nodo_arbol(punto=puntos[mediana])
        if profundidad == 0:
            self.raiz = nodo
        nodo.izq = self.construir_arbol(puntos[:mediana], profundidad + 1)
        nodo.der = self.construir_arbol(puntos[mediana + 1:], profundidad + 1)
        return nodo

    def buscar_min(self, actual, target, nivel, mejorp, mejord):
        if actual is None:
            return mejorp, mejord
        if mejorp is None or self.distancia(actual.punto, target) < mejord:
            mejorp = actual.punto
            mejord = self.distancia(actual.punto, target)
        c = nivel % self.h
        rama = "izq"
        if target[c] <= actual.punto[c]:
            mejorp, mejord = self.buscar_min(actual.izq, target, nivel + 1, mejorp, mejord)
        else:
            mejorp, mejord = self.buscar_min(actual.der, target, nivel + 1, mejorp, mejord)
            rama = "der"
        if mejord > abs(actual.punto[c] - target[c]):
            if rama == "izq":
                mejorp, mejord = self.buscar_min(actual.der, target, nivel + 1, mejorp, mejord)
            else:
                mejorp, mejord = self.buscar_min(actual.izq, target, nivel + 1, mejorp, mejord)
        return mejorp, mejord

    def distancia(self, punto_a, punto_b):
        R = 6371.0
        dlat = math.radians(punto_b[0] - punto_a[0])
        dlon = math.radians(punto_b[1] - punto_a[1])
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(punto_a[0])) * math.cos(math.radians(punto_b[0])) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))

    def busca_radio(self, actual, target, nivel, radio, aptos):
        if actual is None:
            return aptos
        if self.distancia(actual.punto, target) < radio:
            aptos.append(actual.punto)
        c = nivel % self.h
        rama = "izq"
        if target[c] <= actual.punto[c]:
            self.busca_radio(actual.izq, target, nivel + 1, radio, aptos)
        else:
            self.busca_radio(actual.der, target, nivel + 1, radio, aptos)
            rama = "der"
        if radio > abs(actual.punto[c] - target[c]):
            if rama == "izq":
                self.busca_radio(actual.der, target, nivel + 1, radio, aptos)
            else:
                self.busca_radio(actual.izq, target, nivel + 1, radio, aptos)
        return aptos


# ─── Carga de datos ─────────────────────────────────────────────────────────────

def cargar_lugares(archivo="lugares.csv"):
    lugares = {}
    with open(archivo, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lid = int(row["id"])
            lugares[lid] = {
                "nombre": row["nombre"],
                "tipo": row["tipo"],
                "lat": float(row["latitud"]),
                "lon": float(row["longitud"]),
                "rating": float(row["rating"]),
                "tiempo_visita": int(row["tiempo_visita_min"]),
            }
    return lugares


def cargar_conexiones(archivo="conexiones.csv"):
    aristas = []
    with open(archivo, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            aristas.append((
                int(row["origen"]),
                int(row["destino"]),
                int(row["tiempo_min"]),
                int(row["costo_pesos"]),
            ))
    return aristas


def cargar_horarios(archivo="horarios.csv"):
    horarios = {}
    with open(archivo, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            horarios[int(row["id_lugar"])] = {
                "abre": row["abre"],
                "cierra": row["cierra"],
                "dias_cerrado": row["dias_cerrado"],
            }
    return horarios


def cargar_hoteles(archivo="hoteles.csv"):
    hoteles = {}
    with open(archivo, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hid = int(row["id"])
            hoteles[hid] = {
                "nombre": row["nombre"],
                "lat": float(row["latitud"]),
                "lon": float(row["longitud"]),
            }
    return hoteles


# ─── Lógica del planificador ────────────────────────────────────────────────────

def lugares_cercanos(punto_actual, radio_permitido, lugares):
    dicc_puntos = {}
    arbol_puntos = kd_trees(2)
    lista = []
    lugares_result = {}
    for idx in lugares:
        dicc_puntos[idx] = (lugares[idx]["lat"], lugares[idx]["lon"])
    for val in dicc_puntos.values():
        lista.append(val)
    arbol_puntos.construir_arbol(lista, 0)
    aptos = arbol_puntos.busca_radio(arbol_puntos.raiz, punto_actual, 0, radio_permitido, [])
    for key, valor in dicc_puntos.items():
        if valor in aptos:
            lugares_result[key] = lugares[key]
    return lugares_result


def grafo_original(aristas):
    hijos = {}
    for origen, destino, tiempo, costo in aristas:
        if origen not in hijos:
            hijos[origen] = {}
        if destino not in hijos:
            hijos[destino] = {}
        hijos[origen][destino] = tiempo
        hijos[destino][origen] = tiempo
    conexiones_tiempo = grafos()
    conexiones_tiempo.G = hijos
    return conexiones_tiempo


def encontrar_comienzo(opciones, punto_usuario):
    dicc_puntos = {}
    arbol_puntos = kd_trees(2)
    lista = []
    for idx in opciones:
        dicc_puntos[idx] = (opciones[idx]["lat"], opciones[idx]["lon"])
    for val in dicc_puntos.values():
        lista.append(val)
    arbol_puntos.construir_arbol(lista, 0)
    cercano = arbol_puntos.buscar_min(arbol_puntos.raiz, punto_usuario, 0, None, None)
    inicio = 0
    for key, valor in dicc_puntos.items():
        if valor == cercano[0]:
            inicio = key
    return inicio, cercano[1]


def conexiones_artificialesF(inicio_usuario, conexiones_tiempo, opciones):
    pesos = {}
    conexiones_artificiales = {}
    pesos[inicio_usuario], conexiones_artificiales[inicio_usuario] = conexiones_tiempo.dijkstra(inicio_usuario)
    for opcion in opciones:
        pesos[opcion], conexiones_artificiales[opcion] = conexiones_tiempo.dijkstra(opcion)
    return pesos, conexiones_artificiales


def ruta_prim(pesos, opciones, inicio_usuario):
    conexiones_artificiales_grafo = {}
    for idx, valores in pesos.items():
        conexiones_artificiales_grafo[idx] = {}
        for conexion, valor in valores.items():
            if conexion not in conexiones_artificiales_grafo and conexion in opciones.keys():
                conexiones_artificiales_grafo[conexion] = {}
            if valor != float('inf') and valor != 0 and conexion in opciones.keys():
                conexiones_artificiales_grafo[idx][conexion] = valor
    grafo_artificial = grafos()
    grafo_artificial.G = conexiones_artificiales_grafo
    conexiones_optimas = grafo_artificial.prim(inicio_usuario)
    return conexiones_optimas


def reconstruir_camino(pi, destino):
    camino = []
    actual = destino
    while actual is not None:
        camino.append(actual)
        actual = pi[actual]
    camino.reverse()
    return camino


def orden_visita_ponderado(pi, inicio, horarios, lugares):
    hijos_prim = {}
    for nodo in pi:
        hijos_prim[nodo] = []
    for nodo, padre in pi.items():
        if padre is not None:
            hijos_prim[padre].append(nodo)

    orden = []
    pila = [inicio]
    while pila:
        actual = pila.pop()
        orden.append(actual)
        hijos = hijos_prim[actual]
        if len(hijos) == 0:
            continue

        puntajes = {}
        for hijo in hijos:
            puntaje = 0
            if hijo in horarios:
                cierre = int(horarios[hijo]["cierra"].replace(":", ""))
            else:
                cierre = 2359
            puntaje += (2400 - cierre)
            puntaje += (lugares[hijo]["rating"] * 100)
            dist = kd_trees(2)
            punto_a = (lugares[actual]["lat"], lugares[actual]["lon"])
            punto_b = (lugares[hijo]["lat"], lugares[hijo]["lon"])
            km = dist.distancia(punto_a, punto_b)
            puntaje += (100 - km)
            puntaje += lugares[hijo]["tiempo_visita"]
            puntajes[hijo] = puntaje

        hijos_con_puntaje = [(puntajes[h], h) for h in hijos]
        hijos_con_puntaje.sort()
        for _, hijo in hijos_con_puntaje:
            pila.append(hijo)

    return orden


def calcular_hora_max_salida(orden, pesos, horarios, lugares, dist_hotel_km, velocidad_kmh=5):
    tiempo_hotel_inicio = (dist_hotel_km / velocidad_kmh) * 60
    tiempos_llegada = {}
    acumulado = tiempo_hotel_inicio
    tiempos_llegada[orden[0]] = acumulado

    for i in range(len(orden) - 1):
        origen = orden[i]
        destino = orden[i + 1]
        acumulado += lugares[origen]["tiempo_visita"]
        acumulado += pesos[origen][destino]
        tiempos_llegada[destino] = acumulado

    hora_limite = None
    lugar_limitante = None
    for lugar_id, minutos_llegada in tiempos_llegada.items():
        if lugar_id not in horarios:
            continue
        cierre_str = horarios[lugar_id]["cierra"]
        partes = cierre_str.split(":")
        cierre_min = int(partes[0]) * 60 + int(partes[1])
        max_salida = cierre_min - minutos_llegada - lugares[lugar_id]["tiempo_visita"]
        if hora_limite is None or max_salida < hora_limite:
            hora_limite = max_salida
            lugar_limitante = lugar_id

    if hora_limite is None:
        return {
            "hora_limite": None,
            "mensaje": "Ningún lugar tiene restricción de horario, puedes salir a cualquier hora",
            "no_visitables": []
        }

    no_visitables = []
    acumulado = tiempo_hotel_inicio
    tiempos_llegada_real = {}
    tiempos_llegada_real[orden[0]] = acumulado

    for i in range(len(orden) - 1):
        origen = orden[i]
        destino = orden[i + 1]
        hora_llegada_origen = hora_limite + tiempos_llegada_real[origen]
        abierto_origen = True
        if origen in horarios:
            abre_str = horarios[origen]["abre"]
            cierre_str = horarios[origen]["cierra"]
            partes_a = abre_str.split(":")
            partes_c = cierre_str.split(":")
            abre_min = int(partes_a[0]) * 60 + int(partes_a[1])
            cierre_min_o = int(partes_c[0]) * 60 + int(partes_c[1])
            if hora_llegada_origen < abre_min:
                abierto_origen = False
            if hora_llegada_origen + lugares[origen]["tiempo_visita"] > cierre_min_o:
                abierto_origen = False
        if abierto_origen:
            acumulado += lugares[origen]["tiempo_visita"]
        else:
            if origen not in no_visitables:
                no_visitables.append(origen)
        acumulado += pesos[origen][destino]
        tiempos_llegada_real[destino] = acumulado

    ultimo = orden[-1]
    hora_llegada_ultimo = hora_limite + tiempos_llegada_real[ultimo]
    if ultimo in horarios:
        abre_str = horarios[ultimo]["abre"]
        cierre_str = horarios[ultimo]["cierra"]
        partes_a = abre_str.split(":")
        partes_c = cierre_str.split(":")
        abre_min = int(partes_a[0]) * 60 + int(partes_a[1])
        cierre_min_u = int(partes_c[0]) * 60 + int(partes_c[1])
        if hora_llegada_ultimo < abre_min:
            no_visitables.append(ultimo)
        elif hora_llegada_ultimo + lugares[ultimo]["tiempo_visita"] > cierre_min_u:
            no_visitables.append(ultimo)

    horas = int(hora_limite) // 60
    minutos = int(hora_limite) % 60

    return {
        "hora_limite": f"{horas}:{minutos:02d}",
        "lugar_limitante": lugares[lugar_limitante]["nombre"],
        "cierra_limitante": horarios[lugar_limitante]["cierra"],
        "no_visitables": [{"id": lid, "nombre": lugares[lid]["nombre"]} for lid in no_visitables]
    }


# ─── Datos globales ─────────────────────────────────────────────────────────────

lugares = cargar_lugares()
hoteles = cargar_hoteles()
aristas = cargar_conexiones()
horarios = cargar_horarios()

trie_autocompletado = Trie()
for idx, info in lugares.items():
    trie_autocompletado.inserta(info["nombre"])
for idx, info in hoteles.items():
    trie_autocompletado.inserta(info["nombre"])


# ─── Rutas Flask ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/hoteles")
def api_hoteles():
    return jsonify([{"id": k, "nombre": v["nombre"], "lat": v["lat"], "lon": v["lon"]} for k, v in hoteles.items()])


@app.route("/api/lugares")
def api_lugares():
    resultado = []
    for lid, info in lugares.items():
        item = {"id": lid}
        item.update(info)
        if lid in horarios:
            item["horario"] = horarios[lid]
        resultado.append(item)
    return jsonify(resultado)


@app.route("/api/autocompletar")
def api_autocompletar():
    prefijo = request.args.get("q", "")
    if not prefijo:
        return jsonify([])
    resultados = trie_autocompletado.autocompletado(prefijo)
    return jsonify(resultados[:10])


@app.route("/api/lugares_cercanos", methods=["POST"])
def api_lugares_cercanos():
    data = request.json
    hotel_id = data["hotel_id"]
    radio = data["radio"]
    punto = (hoteles[hotel_id]["lat"], hoteles[hotel_id]["lon"])
    cercanos = lugares_cercanos(punto, radio, lugares)
    resultado = []
    for lid, info in cercanos.items():
        item = {"id": lid}
        item.update(info)
        if lid in horarios:
            item["horario"] = horarios[lid]
        resultado.append(item)
    return jsonify(resultado)


@app.route("/api/calcular_ruta", methods=["POST"])
def api_calcular_ruta():
    data = request.json
    hotel_id = data["hotel_id"]
    lugares_ids = data["lugares_ids"]

    punto_usuario = (hoteles[hotel_id]["lat"], hoteles[hotel_id]["lon"])

    opciones_final = {}
    for lid in lugares_ids:
        opciones_final[lid] = lugares[lid]

    conexiones_tiempo = grafo_original(aristas)
    inicio_usuario, distancia_hotel = encontrar_comienzo(opciones_final, punto_usuario)

    pesos, conexiones_artificiales = conexiones_artificialesF(inicio_usuario, conexiones_tiempo, opciones_final)
    conexiones_optimas = ruta_prim(pesos, opciones_final, inicio_usuario)
    orden = orden_visita_ponderado(conexiones_optimas, inicio_usuario, horarios, lugares)

    # Construir ruta detallada
    ruta_detalle = []
    total_tiempo = 0
    for i in range(len(orden) - 1):
        origen = orden[i]
        destino = orden[i + 1]
        pi_real = conexiones_artificiales[origen]
        camino = reconstruir_camino(pi_real, destino)
        tiempo = pesos[origen][destino]
        total_tiempo += tiempo
        nombres_camino = [lugares[n]["nombre"] for n in camino]
        ruta_detalle.append({
            "origen": lugares[origen]["nombre"],
            "destino": lugares[destino]["nombre"],
            "tiempo_min": tiempo,
            "ruta_intermedia": nombres_camino
        })

    info_horario = calcular_hora_max_salida(orden, pesos, horarios, lugares, distancia_hotel)

    orden_nombres = [{"id": lid, "nombre": lugares[lid]["nombre"], "tipo": lugares[lid]["tipo"],
                      "rating": lugares[lid]["rating"], "tiempo_visita": lugares[lid]["tiempo_visita"]}
                     for lid in orden]

    tiempo_hotel_inicio_min = round((distancia_hotel / 5) * 60)
    total_visita_min = sum(lugares[lid]["tiempo_visita"] for lid in orden)

    return jsonify({
        "orden_visita": orden_nombres,
        "ruta_detalle": ruta_detalle,
        "total_traslado_min": total_tiempo,
        "tiempo_hotel_inicio_min": tiempo_hotel_inicio_min,
        "total_visita_min": total_visita_min,
        "horario": info_horario,
        "hotel": hoteles[hotel_id]["nombre"],
        "distancia_hotel_primer_lugar_km": round(distancia_hotel, 2)
    })


if __name__ == "__main__":
    app.run(debug=True, port=8080)
