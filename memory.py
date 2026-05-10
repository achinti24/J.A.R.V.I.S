import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path.home() / ".jarvis_memory.json"

MEMORIA_VACIA = {
    "conversaciones": [],
    "preferencias": {
        "musica_favorita": None,
        "proyecto_frecuente": None,
        "app_frecuente": None,
    },
    "ultimo_proyecto": None,
    "ultima_app": None,
    "ultima_musica": None,
    "contadores": {
        "proyectos": {},
        "apps": {},
        "musica": {}
    },
    "notas": []
}

# ─── Cargar y guardar ────────────────────────────────────────────────────────

def cargar_memoria():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Agrega claves nuevas si faltan
                for key, val in MEMORIA_VACIA.items():
                    if key not in data:
                        data[key] = val
                return data
        except:
            return MEMORIA_VACIA.copy()
    return MEMORIA_VACIA.copy()

def guardar_memoria(memoria):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memoria, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando memoria: {e}")

# ─── Registrar acciones ──────────────────────────────────────────────────────

def recordar_accion(tipo, valor):
    memoria = cargar_memoria()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Actualiza último usado
    if tipo == "proyecto":
        memoria["ultimo_proyecto"] = valor
        memoria["contadores"]["proyectos"][valor] = \
            memoria["contadores"]["proyectos"].get(valor, 0) + 1
    elif tipo == "app":
        memoria["ultima_app"] = valor
        memoria["contadores"]["apps"][valor] = \
            memoria["contadores"]["apps"].get(valor, 0) + 1
    elif tipo == "musica":
        memoria["ultima_musica"] = valor
        memoria["contadores"]["musica"][valor] = \
            memoria["contadores"]["musica"].get(valor, 0) + 1

    # Actualiza preferencias basado en frecuencia
    for categoria, contador_key in [
        ("musica_favorita", "musica"),
        ("proyecto_frecuente", "proyectos"),
        ("app_frecuente", "apps")
    ]:
        contadores = memoria["contadores"][contador_key]
        if contadores:
            memoria["preferencias"][categoria] = max(contadores, key=contadores.get)

    # Agrega al historial
    memoria["conversaciones"].append({
        "fecha": ahora,
        "tipo": tipo,
        "valor": valor
    })
    # Mantiene solo las últimas 100 entradas
    memoria["conversaciones"] = memoria["conversaciones"][-100:]

    guardar_memoria(memoria)

def guardar_nota(nota):
    memoria = cargar_memoria()
    memoria["notas"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "contenido": nota
    })
    memoria["notas"] = memoria["notas"][-50:]
    guardar_memoria(memoria)
    return "Nota guardada, señor."

def obtener_notas():
    memoria = cargar_memoria()
    notas = memoria.get("notas", [])
    if not notas:
        return "No tiene notas guardadas, señor."
    ultimas = notas[-5:]
    resultado = "Sus últimas notas, señor:\n"
    for n in ultimas:
        resultado += f"- [{n['fecha']}] {n['contenido']}\n"
    return resultado

# ─── Contexto para el LLM ────────────────────────────────────────────────────

def obtener_contexto():
    memoria = cargar_memoria()
    partes = []

    if memoria.get("ultimo_proyecto"):
        partes.append(f"Último proyecto abierto: {memoria['ultimo_proyecto']}")

    if memoria.get("ultima_app"):
        partes.append(f"Última app usada: {memoria['ultima_app']}")

    if memoria.get("ultima_musica"):
        partes.append(f"Última música reproducida: {memoria['ultima_musica']}")

    prefs = memoria.get("preferencias", {})
    if prefs.get("proyecto_frecuente"):
        partes.append(f"Proyecto más frecuente: {prefs['proyecto_frecuente']}")
    if prefs.get("musica_favorita"):
        partes.append(f"Música favorita: {prefs['musica_favorita']}")

    return ". ".join(partes) if partes else ""

def obtener_estadisticas():
    memoria = cargar_memoria()
    contadores = memoria.get("contadores", {})
    
    lineas = ["📊 Estadísticas de uso, señor:"]
    
    if contadores.get("proyectos"):
        top = sorted(contadores["proyectos"].items(), key=lambda x: x[1], reverse=True)[:3]
        lineas.append(f"Proyectos más usados: {', '.join([f'{k}({v})' for k,v in top])}")
    
    if contadores.get("musica"):
        top = sorted(contadores["musica"].items(), key=lambda x: x[1], reverse=True)[:3]
        lineas.append(f"Música más reproducida: {', '.join([f'{k}({v})' for k,v in top])}")
    
    total = len(memoria.get("conversaciones", []))
    lineas.append(f"Total de acciones registradas: {total}")
    
    return "\n".join(lineas)