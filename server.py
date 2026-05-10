import threading
import psutil
import requests
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from pathlib import Path

app = Flask(__name__, template_folder='interface')
app.config['SECRET_KEY'] = 'jarvis-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# ─── API del clima ────────────────────────────────────────────────────────────
# Registrate gratis en https://openweathermap.org/api y pon tu API key aquí
WEATHER_API_KEY = "35d7f6d3356ad22da3dcca5096b9d56d"
CIUDAD = "Bogota,CO"

def obtener_clima():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CIUDAD}&appid={WEATHER_API_KEY}&units=metric&lang=es"
        r = requests.get(url, timeout=5)
        data = r.json()
        return {
            "temp": round(data["main"]["temp"]),
            "descripcion": data["weather"][0]["description"].capitalize(),
            "humedad": data["main"]["humidity"],
            "ciudad": data["name"],
            "icono": data["weather"][0]["icon"]
        }
    except:
        return {
            "temp": "--",
            "descripcion": "No disponible",
            "humedad": "--",
            "ciudad": CIUDAD.split(",")[0],
            "icono": "01d"
        }

# ─── Festivos Colombia ────────────────────────────────────────────────────────

FESTIVOS_COLOMBIA = {
    "01-01": "Año Nuevo",
    "01-06": "Reyes Magos",
    "03-24": "Día de San José",
    "04-17": "Jueves Santo",
    "04-18": "Viernes Santo",
    "05-01": "Día del Trabajo",
    "05-13": "Ascensión del Señor",
    "06-02": "Corpus Christi",
    "06-09": "Sagrado Corazón",
    "06-30": "San Pedro y San Pablo",
    "07-04": "Día de la Independencia de Colombia",
    "07-20": "Día de la Independencia",
    "08-07": "Batalla de Boyacá",
    "08-19": "Asunción de la Virgen",
    "10-14": "Día de la Raza",
    "11-04": "Todos los Santos",
    "11-11": "Independencia de Cartagena",
    "12-08": "Inmaculada Concepción",
    "12-25": "Navidad",
}

DIAS_ESPECIALES = {
    "02-14": "Día de San Valentín",
    "03-08": "Día Internacional de la Mujer",
    "04-22": "Día de la Tierra",
    "05-15": "Día del Maestro en Colombia",
    "06-01": "Día del Niño en Colombia",
    "09-16": "Día del Amor y la Amistad",
    "10-31": "Halloween",
    "11-13": "Día de la Mujer en Colombia",
    "12-24": "Nochebuena",
    "12-31": "Nochevieja",
}

def obtener_dia_especial():
    hoy = datetime.now().strftime("%m-%d")
    if hoy in FESTIVOS_COLOMBIA:
        return {"tipo": "festivo", "nombre": FESTIVOS_COLOMBIA[hoy]}
    if hoy in DIAS_ESPECIALES:
        return {"tipo": "especial", "nombre": DIAS_ESPECIALES[hoy]}
    return None

def proximo_festivo():
    hoy = datetime.now()
    mes_dia_hoy = hoy.strftime("%m-%d")
    todos = {**FESTIVOS_COLOMBIA, **DIAS_ESPECIALES}
    proximos = []
    for fecha, nombre in todos.items():
        mes, dia = fecha.split("-")
        fecha_dt = datetime(hoy.year, int(mes), int(dia))
        if fecha_dt < hoy:
            fecha_dt = datetime(hoy.year + 1, int(mes), int(dia))
        dias_restantes = (fecha_dt - hoy).days
        proximos.append({"nombre": nombre, "fecha": fecha, "dias": dias_restantes})
    proximos.sort(key=lambda x: x["dias"])
    return proximos[:3]

# ─── Stats del sistema ────────────────────────────────────────────────────────

def obtener_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disco = psutil.disk_usage('/')
    return {
        "cpu": cpu,
        "ram_usado": round(mem.used / (1024**3), 1),
        "ram_total": round(mem.total / (1024**3), 1),
        "ram_porcentaje": mem.percent,
        "disco_usado": round(disco.used / (1024**3), 1),
        "disco_total": round(disco.total / (1024**3), 1),
        "disco_porcentaje": disco.percent,
    }

# ─── Rutas Flask ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    ahora = datetime.now()
    dia_especial = obtener_dia_especial()
    return jsonify({
        "hora": ahora.strftime("%I:%M:%S %p"),
        "fecha": ahora.strftime("%d de %B de %Y"),
        "dia": ahora.strftime("%A").capitalize(),
        "stats": obtener_stats(),
        "clima": obtener_clima(),
        "dia_especial": dia_especial,
        "proximos_festivos": proximo_festivo(),
        "estado_jarvis": "online"
    })

@app.route('/api/comando', methods=['POST'])
def comando():
    from flask import request
    from brain import procesar
    data = request.json
    texto = data.get('texto', '')
    respuesta = procesar(texto)
    socketio.emit('respuesta_jarvis', {'texto': respuesta})
    return jsonify({'respuesta': respuesta})

# ─── SocketIO eventos ─────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    emit('estado', {'mensaje': 'Conectado a Jarvis'})

@socketio.on('comando_voz')
def on_comando(data):
    from brain import procesar
    respuesta = procesar(data.get('texto', ''))
    emit('respuesta_jarvis', {'texto': respuesta})

def emitir_estado_escucha(estado):
    """Llamar desde main.py para actualizar estado en la UI"""
    socketio.emit('estado_escucha', {'escuchando': estado})

def emitir_transcripcion(texto):
    """Llamar desde main.py para mostrar lo que escuchó"""
    socketio.emit('transcripcion', {'texto': texto})

def emitir_respuesta(texto):
    """Llamar desde main.py para mostrar respuesta de Jarvis"""
    socketio.emit('respuesta_jarvis', {'texto': texto})

def iniciar_servidor():
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    iniciar_servidor()