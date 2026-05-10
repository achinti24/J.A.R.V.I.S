import os
import json
import subprocess
import webbrowser
import difflib
import re
import shutil
from pathlib import Path
from datetime import datetime

# ─── Cargar configuración ───────────────────────────────────────────────────
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DOCS = Path(config["documentos"])

# ─── Palabras clave por categoría ───────────────────────────────────────────
PALABRAS_MUSICA = [
    "música", "musica", "reproduce", "reproducir", "pon", "poner",
    "escuchar", "escucha", "lista", "playlist", "canción", "cancion",
    "song", "play", "suena", "toca", "tocame", "quiero oir", "quiero escuchar"
]

PALABRAS_PROYECTO = [
    "proyecto", "project", "carpeta del proyecto", "abre el proyecto",
    "abrir proyecto", "trabaja en", "trabajar en", "carga el proyecto"
]

PALABRAS_ABRIR = [
    "abre", "abrir", "lanza", "lanzar", "inicia", "iniciar",
    "abre la app", "abre la aplicación", "ejecuta", "corre", "muéstrame"
]

PALABRAS_BUSCAR = [
    "busca", "buscar", "encuentra", "encontrar", "archivo",
    "fichero", "dónde está", "donde está", "localiza", "halla"
]

PALABRAS_SITIO = [
    "ve a", "entra a", "abre la página", "abre el sitio",
    "navega a", "ir a", "visita", "muéstrame la página"
]

PALABRAS_LISTAR = [
    "lista mis proyectos", "cuáles son mis proyectos", "cuales son mis proyectos",
    "qué proyectos tengo", "que proyectos tengo", "muéstrame mis proyectos",
    "muestra mis proyectos", "proyectos disponibles"
]

PALABRAS_SCRIPT = [
    "ejecuta el script", "corre el script", "ejecuta", "corre el archivo",
    "lanza el script", "inicia el script"
]

PALABRAS_VOLUMEN = [
    "sube el volumen", "baja el volumen", "volumen al máximo",
    "silencia", "mutea", "quita el sonido", "pon el sonido"
]

PALABRAS_SCREENSHOT = [
    "captura de pantalla", "screenshot", "toma una foto de la pantalla",
    "captura pantalla", "pantallazo"
]

PALABRAS_HORA = [
    "qué hora es", "que hora es", "dime la hora", "hora actual",
    "qué día es", "que dia es", "fecha de hoy", "qué fecha es"
]

PALABRAS_APAGAR = [
    "apaga el pc", "apaga la computadora", "apagar pc",
    "reinicia el pc", "reiniciar pc", "bloquea la pantalla",
    "bloquear pantalla", "suspende el pc"
]

# ─── Utilidades ─────────────────────────────────────────────────────────────

def contiene_alguna(texto, palabras):
    texto = texto.lower()
    return any(p in texto for p in palabras)

def coincidencia_fuzzy(nombre, opciones, umbral=0.45):
    nombre = nombre.lower()
    opciones_lower = [o.lower() for o in opciones]
    coincidencias = difflib.get_close_matches(nombre, opciones_lower, n=1, cutoff=umbral)
    if coincidencias:
        idx = opciones_lower.index(coincidencias[0])
        return opciones[idx]
    return None

def limpiar_texto(texto, palabras_remover):
    texto = texto.lower()
    for p in sorted(palabras_remover, key=len, reverse=True):
        texto = texto.replace(p, "")
    return re.sub(r'\s+', ' ', texto).strip()

# ─── Proyectos ───────────────────────────────────────────────────────────────

def listar_proyectos():
    try:
        proyectos = [p.name for p in DOCS.iterdir() if p.is_dir()]
        if not proyectos:
            return "No encontré proyectos en su carpeta de documentos, señor."
        return f"Tiene {len(proyectos)} proyectos, señor: {', '.join(proyectos)}."
    except Exception as e:
        return f"Error listando proyectos: {e}"

def encontrar_proyecto(nombre):
    try:
        proyectos = [p for p in DOCS.iterdir() if p.is_dir()]
        nombres = [p.name for p in proyectos]
        coincidencia = coincidencia_fuzzy(nombre, nombres, umbral=0.4)
        if coincidencia:
            for p in proyectos:
                if p.name.lower() == coincidencia.lower():
                    return p
    except Exception as e:
        print(f"Error buscando proyecto: {e}")
    return None

def abrir_proyecto(nombre):
    if not nombre:
        return "¿Cuál proyecto desea abrir, señor?"
    proyecto = encontrar_proyecto(nombre)
    if proyecto:
        vscode = config["apps"].get("vscode", "code")
        try:
            subprocess.Popen([vscode, str(proyecto)])
            return f"Abriendo proyecto {proyecto.name} en VS Code, señor."
        except Exception as e:
            # Intenta con el comando 'code' directamente
            try:
                subprocess.Popen(["code", str(proyecto)])
                return f"Abriendo proyecto {proyecto.name}, señor."
            except:
                os.startfile(str(proyecto))
                return f"Abriendo carpeta del proyecto {proyecto.name}, señor."
    return f"No encontré ningún proyecto llamado '{nombre}', señor. ¿Quiere que liste los disponibles?"

# ─── Aplicaciones ────────────────────────────────────────────────────────────

def abrir_app(nombre):
    apps = config.get("apps", {})
    coincidencia = coincidencia_fuzzy(nombre, list(apps.keys()), umbral=0.4)
    if coincidencia:
        ruta = apps[coincidencia]
        try:
            subprocess.Popen([ruta])
            return f"Abriendo {coincidencia}, señor."
        except Exception as e:
            try:
                os.startfile(ruta)
                return f"Abriendo {coincidencia}, señor."
            except:
                return f"No pude abrir {coincidencia}: {e}"
    # Intenta abrir por nombre directamente
    try:
        subprocess.Popen([nombre])
        return f"Abriendo {nombre}, señor."
    except:
        return f"No encontré la aplicación '{nombre}', señor."

# ─── Sitios web ──────────────────────────────────────────────────────────────

def abrir_sitio(nombre):
    sitios = config.get("sitios", {})
    coincidencia = coincidencia_fuzzy(nombre, list(sitios.keys()), umbral=0.4)
    if coincidencia:
        webbrowser.open(sitios[coincidencia])
        return f"Abriendo {coincidencia}, señor."
    # Busca en Google si no reconoce
    webbrowser.open(f"https://www.google.com/search?q={nombre}")
    return f"Buscando '{nombre}' en Google, señor."

# ─── Música ──────────────────────────────────────────────────────────────────

def poner_musica(genero=None):
    musica = config.get("musica", {})
    if not musica:
        webbrowser.open("https://www.youtube.com")
        return "Abriendo YouTube, señor."
    
    if genero:
        coincidencia = coincidencia_fuzzy(genero, list(musica.keys()), umbral=0.35)
        if coincidencia:
            webbrowser.open(musica[coincidencia])
            return f"Reproduciendo {coincidencia}, señor."
        # Busca en YouTube si no está en la config
        webbrowser.open(f"https://www.youtube.com/results?search_query={genero}")
        return f"Buscando '{genero}' en YouTube, señor."
    
    # Sin género específico abre la primera lista
    primera_key = list(musica.keys())[0]
    webbrowser.open(musica[primera_key])
    return f"Reproduciendo {primera_key}, señor."

def extraer_genero_musica(texto):
    musica = config.get("musica", {})
    texto_lower = texto.lower()
    
    # Busca coincidencia exacta primero
    for genero in musica.keys():
        if genero.lower() in texto_lower:
            return genero
    
    # Limpia palabras comunes y busca fuzzy
    palabras_remover = PALABRAS_MUSICA + ["de", "la", "el", "un", "una", "algo", "quiero", "por favor"]
    texto_limpio = limpiar_texto(texto, palabras_remover)
    
    if texto_limpio:
        return texto_limpio
    return None

# ─── Archivos ────────────────────────────────────────────────────────────────

def buscar_archivo(nombre):
    if not nombre:
        return "¿Qué archivo desea buscar, señor?"
    try:
        resultados = list(DOCS.rglob(f"*{nombre}*"))
        if resultados:
            os.startfile(str(resultados[0].parent))
            nombres = [r.name for r in resultados[:5]]
            return f"Encontré {len(resultados)} archivo(s). Abriendo ubicación. Los primeros son: {', '.join(nombres)}, señor."
        return f"No encontré ningún archivo con '{nombre}' en el nombre, señor."
    except Exception as e:
        return f"Error buscando archivo: {e}"

# ─── Scripts ─────────────────────────────────────────────────────────────────

def ejecutar_script(ruta):
    if not ruta:
        return "¿Qué script desea ejecutar, señor?"
    try:
        if not ruta.endswith(".py"):
            ruta += ".py"
        ruta_completa = Path(ruta)
        if not ruta_completa.exists():
            # Busca en documentos
            resultados = list(DOCS.rglob(f"*{ruta}*"))
            if resultados:
                ruta_completa = resultados[0]
            else:
                return f"No encontré el script '{ruta}', señor."
        subprocess.Popen(
            ["python", str(ruta_completa)],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return f"Ejecutando {ruta_completa.name}, señor."
    except Exception as e:
        return f"No pude ejecutar el script: {e}"

# ─── Sistema ─────────────────────────────────────────────────────────────────

def obtener_hora_fecha():
    ahora = datetime.now()
    hora = ahora.strftime("%I:%M %p")
    fecha = ahora.strftime("%A %d de %B de %Y")
    return f"Son las {hora} del {fecha}, señor."

def captura_pantalla():
    try:
        import pyautogui
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = Path.home() / "Pictures" / f"jarvis_screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(str(ruta))
        os.startfile(str(ruta.parent))
        return f"Captura guardada como {ruta.name}, señor."
    except Exception as e:
        return f"No pude tomar la captura: {e}"

def control_sistema(accion):
    acciones = {
        "apagar": "shutdown /s /t 10",
        "reiniciar": "shutdown /r /t 10",
        "bloquear": "rundll32.exe user32.dll,LockWorkStation",
        "suspender": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
    }
    for key, cmd in acciones.items():
        if key in accion:
            os.system(cmd)
            return f"Ejecutando {key} del sistema, señor."
    return None

# ─── Procesador principal ────────────────────────────────────────────────────

def procesar_accion(texto):
    if not texto:
        return None
    
    t = texto.lower().strip()

    # Hora y fecha
    if contiene_alguna(t, PALABRAS_HORA):
        return obtener_hora_fecha()

    # Captura de pantalla
    if contiene_alguna(t, PALABRAS_SCREENSHOT):
        return captura_pantalla()

    # Control del sistema
    if contiene_alguna(t, PALABRAS_APAGAR):
        return control_sistema(t)

    # Listar proyectos
    if contiene_alguna(t, PALABRAS_LISTAR):
        return listar_proyectos()

    # Música — detección prioritaria
    if contiene_alguna(t, PALABRAS_MUSICA):
        genero = extraer_genero_musica(t)
        return poner_musica(genero)

    # Proyectos
    if contiene_alguna(t, PALABRAS_PROYECTO):
        palabras_remover = PALABRAS_PROYECTO + PALABRAS_ABRIR + ["el", "la", "un", "una", "mi", "en", "vscode", "code"]
        nombre = limpiar_texto(t, palabras_remover)
        return abrir_proyecto(nombre)

    # Apps conocidas — revisa si menciona alguna directamente
    apps = config.get("apps", {})
    for app in apps.keys():
        if app.lower() in t:
            return abrir_app(app)

    # Sitios conocidos — revisa si menciona alguno directamente
    sitios = config.get("sitios", {})
    for sitio in sitios.keys():
        if sitio.lower() in t:
            return abrir_sitio(sitio)

    # Abrir genérico
    if contiene_alguna(t, PALABRAS_ABRIR):
        palabras_remover = PALABRAS_ABRIR + ["el", "la", "un", "una", "por favor"]
        nombre = limpiar_texto(t, palabras_remover)
        if nombre:
            # Intenta app primero, luego sitio
            resultado_app = abrir_app(nombre)
            if "No encontré" not in resultado_app:
                return resultado_app
            return abrir_sitio(nombre)

    # Buscar archivos
    if contiene_alguna(t, PALABRAS_BUSCAR):
        palabras_remover = PALABRAS_BUSCAR + ["el", "la", "un", "una", "por favor", "archivo", "fichero"]
        nombre = limpiar_texto(t, palabras_remover)
        return buscar_archivo(nombre)

    # Scripts
    if contiene_alguna(t, PALABRAS_SCRIPT):
        palabras_remover = PALABRAS_SCRIPT + ["el", "la", "un", "una", "por favor", "python"]
        nombre = limpiar_texto(t, palabras_remover)
        return ejecutar_script(nombre)

    # Sitios web genérico
    if contiene_alguna(t, PALABRAS_SITIO):
        palabras_remover = PALABRAS_SITIO + ["el", "la", "un", "una", "por favor"]
        nombre = limpiar_texto(t, palabras_remover)
        return abrir_sitio(nombre)

    return None