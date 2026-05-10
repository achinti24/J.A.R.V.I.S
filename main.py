import time
import sys
import os
import threading
import webbrowser
from datetime import datetime
from listener import (
    escuchar, escuchar_rapido, contiene_wake_word,
    contiene_descanso, limpiar_wake_word, calibrar_microfono
)
from brain import procesar, limpiar_historial
from speaker import hablar, hablar_rapido
from memory import (
    recordar_accion, obtener_contexto,
    guardar_nota, obtener_notas, obtener_estadisticas
)

# ─── Importa servidor e interfaz ─────────────────────────────────────────────
try:
    from server import (
        iniciar_servidor,
        emitir_transcripcion,
        emitir_respuesta,
        emitir_estado_escucha
    )
    SERVIDOR_DISPONIBLE = True
except Exception as e:
    print(f"⚠️  Servidor de interfaz no disponible: {e}")
    SERVIDOR_DISPONIBLE = False

    # Funciones vacías si no hay servidor
    def emitir_transcripcion(t): pass
    def emitir_respuesta(t): pass
    def emitir_estado_escucha(e): pass

# ─── Configuración ────────────────────────────────────────────────────────────

VERSION = "2.0"
NOMBRE = "Jarvis"

FRASES_ACTIVACION = [
    "Dígame, señor.",
    "A sus órdenes, señor.",
    "¿En qué puedo ayudarle, señor?",
    "Escuchando, señor.",
    "Presente, señor.",
    "Listo para asistirle, señor.",
]

COMANDOS_ESPECIALES_KEYWORDS = {
    "estadísticas": obtener_estadisticas,
    "estadisticas": obtener_estadisticas,
    "mis notas": obtener_notas,
    "notas": obtener_notas,
}

import random

def frase_activacion_aleatoria():
    return random.choice(FRASES_ACTIVACION)

# ─── Banner ───────────────────────────────────────────────────────────────────

def mostrar_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
\033[94m
    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
    ██║███████║██████╔╝██║   ██║██║███████╗
    ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
    ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
    ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
\033[0m
    \033[92mv{VERSION} — Asistente Personal de IA\033[0m
    \033[90m{datetime.now().strftime("%A, %d de %B de %Y — %H:%M")}\033[0m
    """)

# ─── Comandos especiales ──────────────────────────────────────────────────────

def verificar_comando_especial(texto):
    """Verifica si es un comando interno de Jarvis"""
    texto_lower = texto.lower().strip()

    # Guardar nota
    if any(w in texto_lower for w in ["anota", "guarda una nota", "recuerda que", "apunta"]):
        nota = texto_lower
        for w in ["anota", "guarda una nota", "recuerda que", "apunta"]:
            nota = nota.replace(w, "")
        nota = nota.strip()
        if nota:
            return guardar_nota(nota)
        return "¿Qué desea que anote, señor?"

    # Leer notas
    if any(w in texto_lower for w in ["mis notas", "lee mis notas", "qué notas tengo", "que notas tengo"]):
        return obtener_notas()

    # Estadísticas
    if any(w in texto_lower for w in ["estadísticas", "estadisticas", "cuánto has hecho", "cuanto has hecho"]):
        return obtener_estadisticas()

    # Nueva conversación
    if any(w in texto_lower for w in ["nueva conversación", "nueva conversacion", "olvida lo anterior", "reinicia"]):
        limpiar_historial()
        return "Conversación reiniciada, señor. ¿En qué puedo ayudarle?"

    return None

# ─── Modo conversación ────────────────────────────────────────────────────────

def modo_conversacion():
    """
    Modo activo — escucha continuamente hasta que el usuario diga descansa.
    No requiere repetir 'Jarvis' para cada orden.
    """
    print("\n\033[92m💬 Modo conversación activo\033[0m")
    print("\033[90m   Di 'descansa' para volver al modo espera\033[0m\n")

    frase = frase_activacion_aleatoria()
    hablar(frase)
    emitir_respuesta(frase)

    sin_respuesta = 0

    while True:
        try:
            # Notifica a la interfaz que está escuchando
            emitir_estado_escucha(True)

            texto = escuchar(timeout=12, duracion_max=20)

            # Notifica que dejó de escuchar activamente
            emitir_estado_escucha(False)

            # No escuchó nada
            if not texto:
                sin_respuesta += 1
                if sin_respuesta >= 5:
                    msg = "¿Sigue ahí, señor?"
                    hablar_rapido(msg)
                    emitir_respuesta(msg)
                    sin_respuesta = 0
                continue

            sin_respuesta = 0

            # Muestra transcripción en la interfaz
            emitir_transcripcion(texto)

            # Verifica si quiere que descanse
            if contiene_descanso(texto):
                print("\n\033[90m😴 Jarvis en espera...\033[0m\n")
                msg = "Entendido, señor. Aquí estaré cuando me necesite."
                hablar(msg)
                emitir_respuesta(msg)
                emitir_estado_escucha(False)
                limpiar_historial()
                return

            # Limpia wake word si la repitió
            orden = limpiar_wake_word(texto)
            if not orden:
                orden = texto

            if not orden.strip():
                hablar_rapido("Dígame, señor.")
                continue

            # Verifica comandos especiales primero
            resultado_especial = verificar_comando_especial(orden)
            if resultado_especial:
                print(f"\033[96m💬 Jarvis: {resultado_especial}\033[0m")
                hablar(resultado_especial)
                emitir_respuesta(resultado_especial)
                continue

            # Procesa con el cerebro principal
            print(f"\033[93m🧠 Procesando: {orden}\033[0m")
            respuesta = procesar(orden)

            if respuesta:
                print(f"\033[96m💬 Jarvis: {respuesta}\033[0m")
                hablar(respuesta)
                emitir_respuesta(respuesta)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"\033[91mError en conversación: {e}\033[0m")
            time.sleep(0.5)

# ─── Modo espera ──────────────────────────────────────────────────────────────

def modo_espera():
    """
    Modo pasivo — solo escucha la wake word 'Jarvis'.
    Consume mínimos recursos.
    """
    print("\033[90m⏳ En espera... (di 'Jarvis' para activar)\033[0m")
    emitir_estado_escucha(False)

    while True:
        texto = escuchar(timeout=15, duracion_max=5, ajuste_ruido=False)

        if not texto:
            continue

        if contiene_wake_word(texto):
            print(f"\n\033[92m⚡ ¡Activado!\033[0m")
            emitir_transcripcion(texto)

            # Si la orden viene en el mismo texto que el wake word
            orden_inline = limpiar_wake_word(texto)
            if orden_inline and len(orden_inline) > 2:
                print(f"\033[93m🧠 Procesando orden inline: {orden_inline}\033[0m")

                resultado_especial = verificar_comando_especial(orden_inline)
                if resultado_especial:
                    hablar(resultado_especial)
                    emitir_respuesta(resultado_especial)
                else:
                    respuesta = procesar(orden_inline)
                    if respuesta:
                        print(f"\033[96m💬 Jarvis: {respuesta}\033[0m")
                        hablar(respuesta)
                        emitir_respuesta(respuesta)

            return  # Sale del modo espera para entrar a conversación

# ─── Inicialización ───────────────────────────────────────────────────────────

def iniciar():
    """Inicialización completa del sistema"""
    mostrar_banner()

    print("\033[93m🔧 Iniciando sistemas...\033[0m")

    # Arranca servidor de interfaz en hilo separado
    if SERVIDOR_DISPONIBLE:
        print("\033[93m🌐 Iniciando interfaz web...\033[0m")
        hilo_server = threading.Thread(target=iniciar_servidor, daemon=True)
        hilo_server.start()
        time.sleep(2)  # Espera que el servidor arranque
        webbrowser.open("http://127.0.0.1:5000")
        print("\033[92m✅ Interfaz web disponible en http://127.0.0.1:5000\033[0m")

    # Calibra micrófono
    calibrar_microfono()

    print("\033[92m✅ Todos los sistemas en línea.\033[0m")
    print("\033[94m🟢 Jarvis listo. Di 'Jarvis' para activarme.\033[0m\n")

    msg = f"Jarvis versión {VERSION} en línea. Sistemas operativos al cien por ciento. A sus órdenes, señor."
    hablar(msg)
    if SERVIDOR_DISPONIBLE:
        time.sleep(0.5)
        emitir_respuesta(msg)

# ─── Loop principal ───────────────────────────────────────────────────────────

def loop_principal():
    """Loop principal — alterna entre modo espera y modo conversación"""
    iniciar()

    while True:
        try:
            # MODO ESPERA — solo escucha wake word
            modo_espera()

            # MODO CONVERSACIÓN — escucha todo continuamente
            modo_conversacion()

        except KeyboardInterrupt:
            print("\n\n\033[91m👋 Apagando Jarvis...\033[0m")
            hablar("Hasta luego, señor. Que tenga un excelente día.")
            sys.exit(0)

        except Exception as e:
            print(f"\033[91m❌ Error crítico: {e}\033[0m")
            time.sleep(2)
            print("\033[93m🔄 Reiniciando...\033[0m")

# ─── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    loop_principal()