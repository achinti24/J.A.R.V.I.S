import os
import re
import sys
import asyncio
import subprocess
import tempfile
from pathlib import Path

# ─── Configuración de voz ────────────────────────────────────────────────────

# Voz estilo Jarvis en español — masculina, profunda y seria
VOZ_ACTIVA = "es-ES-AlvaroNeural"   # Español España — masculina formal
VELOCIDAD = "-5%"                    # Ligeramente más lento = más serio
TONO = "-10Hz"                       # Más grave = más icónico

FFPLAY = r"C:\ffmpeg\bin\ffplay.exe"

# ─── Reproductor de audio ────────────────────────────────────────────────────

def reproducir_audio(ruta_archivo):
    """Reproduce audio usando ffplay"""
    try:
        proc = subprocess.Popen(
            [FFPLAY, "-nodisp", "-autoexit", "-loglevel", "quiet", ruta_archivo],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        proc.wait(timeout=30)
    except Exception as e:
        print(f"Error reproduciendo audio: {e}")
        _fallback_voz_sistema(ruta_archivo)

def _fallback_voz_sistema(ruta_archivo):
    """Fallback usando PowerShell si ffplay falla"""
    try:
        subprocess.run([
            "powershell", "-NoProfile", "-Command",
            f'$p = New-Object System.Windows.Media.MediaPlayer; '
            f'$p.Open([Uri]::new("{ruta_archivo}")); '
            f'$p.Play(); Start-Sleep 5; $p.Close()'
        ], capture_output=True, timeout=10)
    except:
        pass

# ─── Edge TTS ────────────────────────────────────────────────────────────────

async def _generar_audio_async(texto, archivo_salida):
    """Genera audio con Edge TTS"""
    import edge_tts
    communicate = edge_tts.Communicate(
        texto,
        VOZ_ACTIVA,
        rate=VELOCIDAD,
        pitch=TONO
    )
    await communicate.save(archivo_salida)

def generar_audio_edge(texto, archivo_salida):
    """Wrapper síncrono"""
    try:
        asyncio.run(_generar_audio_async(texto, archivo_salida))
        return True
    except Exception as e:
        print(f"Error generando audio Edge TTS: {e}")
        return False

# ─── Limpieza de texto ───────────────────────────────────────────────────────

def limpiar_texto_para_voz(texto):
    """Limpia el texto para que suene natural"""
    # Elimina emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F9FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    texto = emoji_pattern.sub('', texto)

    # Elimina markdown
    texto = re.sub(r'\*+', '', texto)
    texto = re.sub(r'#+\s?', '', texto)
    texto = re.sub(r'`+', '', texto)
    texto = re.sub(r'\[|\]|\(|\)', '', texto)
    texto = re.sub(r'_{1,2}', '', texto)

    # Elimina JSON que se haya colado
    texto = re.sub(r'\{.*?\}', '', texto, flags=re.DOTALL)

    # Limpia líneas vacías y espacios múltiples
    texto = re.sub(r'\n+', '. ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Limita longitud para no hablar demasiado
    if len(texto) > 500:
        texto = texto[:500] + "."

    return texto

# ─── Funciones públicas ───────────────────────────────────────────────────────

def hablar(texto, velocidad=None):
    """Función principal — habla el texto con voz de Jarvis en español"""
    if not texto:
        return

    texto_limpio = limpiar_texto_para_voz(texto)
    if not texto_limpio:
        return

    print(f"\033[96m🔊 Jarvis: {texto}\033[0m")

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        exito = generar_audio_edge(texto_limpio, temp_path)

        if exito and Path(temp_path).exists():
            reproducir_audio(temp_path)
            try:
                os.unlink(temp_path)
            except:
                pass
        else:
            _fallback_pyttsx3(texto_limpio)

    except Exception as e:
        print(f"Error en hablar: {e}")
        _fallback_pyttsx3(texto_limpio)

def hablar_rapido(texto):
    """Para confirmaciones cortas"""
    hablar(texto)

def hablar_lento(texto):
    """Para información importante"""
    hablar(texto)

def _fallback_pyttsx3(texto):
    """Voz de respaldo si Edge TTS falla"""
    try:
        import pyttsx3
        motor = pyttsx3.init()
        voices = motor.getProperty('voices')
        for v in voices:
            if 'spanish' in v.name.lower() or 'es' in v.id.lower():
                motor.setProperty('voice', v.id)
                break
        motor.setProperty('rate', 160)
        motor.setProperty('volume', 1.0)
        motor.say(texto)
        motor.runAndWait()
        motor.stop()
    except Exception as e:
        print(f"Error en fallback pyttsx3: {e}")

def listar_voces():
    print("\n🎤 Voces estilo Jarvis en español:")
    print("  - es-ES-AlvaroNeural    ← Activa — masculina España formal")
    print("  - es-MX-JorgeNeural     — masculina México")
    print("  - es-CO-GonzaloNeural   — masculina Colombia")
    print("  - es-AR-TomasNeural     — masculina Argentina")
    print(f"\n  Voz activa: {VOZ_ACTIVA}")

def probar_voz():
    hablar("Jarvis en línea. Sistemas operativos al cien por ciento. A sus órdenes, señor.")