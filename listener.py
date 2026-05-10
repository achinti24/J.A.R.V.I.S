import os
import sys
import tempfile
import asyncio
from faster_whisper import WhisperModel
import speech_recognition as sr
from pathlib import Path

# Agrega ffmpeg al PATH
os.environ["PATH"] += r";C:\ffmpeg\bin"

# ─── Correcciones de reconocimiento ─────────────────────────────────────────

CORRECCIONES = {

    # ── Wake word ──────────────────────────────────────────────────────────
    "garbis": "jarvis",
    "garbys": "jarvis",
    "garvis": "jarvis",
    "jarwis": "jarvis",
    "jarbes": "jarvis",
    "jarbi": "jarvis",
    "harvey": "jarvis",
    "jar vis": "jarvis",
    "jarbis": "jarvis",
    "jervis": "jarvis",
    "jarviz": "jarvis",
    "jarvus": "jarvis",
    "javis": "jarvis",
    "jairus": "jarvis",
    "joris": "jarvis",
    "charis": "jarvis",
    "jar is": "jarvis",
    "jaivis": "jarvis",
    "jarvist": "jarvis",
    "chyrus": "jarvis",
    "yarviz": "jarvis",
    "yarvis": "jarvis",

    # ── Tus proyectos ──────────────────────────────────────────────────────
    "kazakas": "casacas",
    "kazacas": "casacas",
    "cassacas": "casacas",
    "kasacas": "casacas",
    "casacax": "casacas",
    "cazacas": "casacas",
    "casaca": "casacas",
    "casacar": "casacas",
    "casacaz": "casacas",
    "kazaka": "casacas",
    "kasaka": "casacas",

    # ── Comandos de apertura ───────────────────────────────────────────────
    "habre": "abre",
    "habré": "abre",
    "havré": "abre",
    "abré": "abre",
    "abrí": "abre",
    "abril": "abre",
    "ábreme": "abre",
    "abreme": "abre",
    "abrirme": "abre",
    "abraza": "abre",
    "habres": "abre",
    "habrir": "abrir",

    # ── Música ────────────────────────────────────────────────────────────
    "reproduse": "reproduce",
    "reprodusé": "reproduce",
    "reproduzca": "reproduce",
    "reproducé": "reproduce",
    "repoduce": "reproduce",
    "repruduce": "reproduce",
    "repoduse": "reproduce",
    "reprodusir": "reproducir",
    "musiga": "música",
    "musica": "música",
    "muzica": "música",
    "mussica": "música",
    "muzika": "música",
    "musika": "música",
    "pond": "pon",
    "ponga": "pon",
    "alabansa": "alabanza",
    "adorasion": "adoración",
    "adoracion": "adoración",
    "adorasión": "adoración",
    "twenty one": "twenty one pilots",
    "twenty 1": "twenty one pilots",
    "21 pilots": "twenty one pilots",
    "veintiuno pilots": "twenty one pilots",

    # ── Aplicaciones ──────────────────────────────────────────────────────
    "crom": "chrome",
    "cromo": "chrome",
    "krome": "chrome",
    "crhome": "chrome",
    "el navegador": "chrome",
    "navegador": "chrome",
    "wor": "word",
    "güord": "word",
    "uord": "word",
    "work": "word",
    "watts app": "whatsapp",
    "watsap": "whatsapp",
    "watsapp": "whatsapp",
    "what sap": "whatsapp",
    "wasap": "whatsapp",
    "wasapp": "whatsapp",
    "güasap": "whatsapp",
    "güatsap": "whatsapp",
    "la terminal": "terminal",
    "consola": "terminal",
    "la consola": "terminal",
    "cmd": "terminal",
    "visual studio code": "vscode",
    "visual estudio": "vscode",
    "visual studio": "vscode",
    "vs code": "vscode",
    "viscode": "vscode",
    "bscode": "vscode",
    "vés code": "vscode",
    "bi code": "vscode",

    # ── Sitios web ────────────────────────────────────────────────────────
    "you tube": "youtube",
    "yutube": "youtube",
    "yutu": "youtube",
    "youtub": "youtube",
    "you tuve": "youtube",
    "you tubo": "youtube",
    "crunchyrol": "crunchyroll",
    "crunchirrol": "crunchyroll",
    "crunchi": "crunchyroll",
    "crunchroll": "crunchyroll",
    "crunch roll": "crunchyroll",
    "krunchirol": "crunchyroll",
    "git hub": "github",
    "githup": "github",
    "get hub": "github",
    "guithub": "github",
    "gitjub": "github",
    "gi mail": "gmail",
    "ge mail": "gmail",
    "yimail": "gmail",
    "correo": "gmail",
    "el correo": "gmail",
    "mi correo": "gmail",

    # ── Comandos de búsqueda ───────────────────────────────────────────────
    "buskar": "busca",
    "buscas": "busca",
    "busque": "busca",
    "encuéntra": "encuentra",
    "localisa": "localiza",
    "localizar": "localiza",

    # ── Comandos de sistema ────────────────────────────────────────────────
    "ke hora es": "qué hora es",
    "que ora es": "qué hora es",
    "que hora es": "qué hora es",
    "dime la ora": "dime la hora",
    "pantallaso": "captura de pantalla",
    "pantallazo": "captura de pantalla",
    "screenshot": "captura de pantalla",
    "apaga la pc": "apaga el pc",
    "apaga la computadora": "apaga el pc",
    "apaga el computador": "apaga el pc",
    "blokea": "bloquea",
    "suspende": "suspende",

    # ── Comandos de descanso ───────────────────────────────────────────────
    "descansa ya": "descansa",
    "que descanses": "descansa",
    "puedes descansar": "descansa",
    "retírate": "descansa",
    "retirate": "descansa",
    "hasta luego jarvis": "descansa",
    "bye": "descansa",
    "chao": "descansa",
    "chao jarvis": "descansa",
    "eso es todo jarvis": "descansa",
    "eso es todo": "descansa",
    "por ahora es todo": "descansa",
    "puedes irte": "descansa",
    "reposa": "descansa",
    "hasta pronto": "descansa",

    # ── Palabras comunes mal reconocidas ──────────────────────────────────
    "porfavor": "por favor",
    "porfa": "por favor",
    "nesesito": "necesito",
    "muestrame": "muéstrame",
    "kiero": "quiero",
    "quero": "quiero",
    "qiero": "quiero",
    "hagame": "hazme",
    "hágame": "hazme",
    "hasme": "hazme",
    "haslo": "hazlo",

    # ── Archivos ──────────────────────────────────────────────────────────
    "punto pi": ".py",
    "punto pie": ".py",
    "punto pai": ".py",
    "punto poy": ".py",
    "punto j son": ".json",
    "punto json": ".json",
    "punto jayson": ".json",
}

def aplicar_correcciones(texto):
    """Corrige palabras mal reconocidas por Whisper"""
    if not texto:
        return texto
    resultado = texto.lower().strip()
    for error, correcto in sorted(CORRECCIONES.items(), key=lambda x: len(x[0]), reverse=True):
        resultado = resultado.replace(error, correcto)
    return resultado

# ─── Configuración ───────────────────────────────────────────────────────────

WAKE_WORDS = [
    "jarvis", "jarvi", "jarbis", "garbis", "jarwis",
    "jarbes", "jarbi", "harvey", "jar vis", "yarvis"
]

PALABRAS_DESCANSO = [
    "descansa", "hasta luego", "adiós", "adios",
    "cuando te necesite", "te llamo", "eso es todo",
    "puedes descansar", "retírate", "retirate",
    "por ahora es todo", "gracias jarvis", "puedes irte",
    "hasta pronto", "bye", "chao", "reposa"
]

# ─── Cargar modelo Whisper ───────────────────────────────────────────────────

print("🎤 Cargando modelo de voz Whisper...")
try:
    modelo_whisper = WhisperModel("medium", device="cpu", compute_type="int8")
    print("✅ Modelo Whisper listo.")
except Exception as e:
    print(f"❌ Error cargando Whisper: {e}")
    sys.exit(1)

# ─── Reconocedor de audio ────────────────────────────────────────────────────

recognizer = sr.Recognizer()
recognizer.energy_threshold = 250
recognizer.pause_threshold = 0.8
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5

# ─── Funciones de audio ──────────────────────────────────────────────────────

def obtener_microfono():
    try:
        mics = sr.Microphone.list_microphone_names()
        print(f"🎙️ Micrófonos disponibles: {len(mics)}")
        return sr.Microphone(sample_rate=16000)
    except Exception as e:
        print(f"Error obteniendo micrófono: {e}")
        return sr.Microphone()

def audio_a_texto(audio):
    """Convierte audio a texto usando faster-whisper"""
    try:
        wav_data = audio.get_wav_data(convert_rate=16000, convert_width=2)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_data)
            temp_path = f.name

        segments, info = modelo_whisper.transcribe(
            temp_path,
            language="es",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        os.unlink(temp_path)

        texto = " ".join([s.text for s in segments]).strip()

        if not texto:
            return None

        # Aplica correcciones
        texto = aplicar_correcciones(texto)

        print(f"📝 Escuché: '{texto}'")
        return texto

    except Exception as e:
        print(f"Error transcribiendo: {e}")
        return None

def escuchar(timeout=10, duracion_max=15, ajuste_ruido=True):
    """Escucha el micrófono y devuelve texto"""
    try:
        with obtener_microfono() as source:
            if ajuste_ruido:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
            print("🎤 Escuchando...")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=duracion_max
                )
            except sr.WaitTimeoutError:
                return None

        return audio_a_texto(audio)

    except Exception as e:
        print(f"Error escuchando: {e}")
        return None

def escuchar_rapido(timeout=8, duracion_max=10):
    return escuchar(timeout=timeout, duracion_max=duracion_max, ajuste_ruido=False)

# ─── Detección de palabras clave ─────────────────────────────────────────────

def contiene_wake_word(texto):
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(w in texto_lower for w in WAKE_WORDS)

def contiene_descanso(texto):
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(w in texto_lower for w in PALABRAS_DESCANSO)

def limpiar_wake_word(texto):
    if not texto:
        return ""
    resultado = texto.lower()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        resultado = resultado.replace(w, "")
    resultado = resultado.lstrip(" ,.-¿?¡!")
    return resultado.strip()

def calibrar_microfono():
    print("🎙️ Calibrando micrófono... (silencio por favor)")
    try:
        with obtener_microfono() as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"✅ Calibrado. Umbral: {recognizer.energy_threshold:.0f}")
        return True
    except Exception as e:
        print(f"Error calibrando: {e}")
        return False

def listar_microfonos():
    mics = sr.Microphone.list_microphone_names()
    for i, mic in enumerate(mics):
        print(f"{i}: {mic}")
    return mics