import requests
import json
import re
from actions import procesar_accion
from memory import obtener_contexto, recordar_accion

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

SYSTEM_PROMPT = """Eres Jarvis, asistente de IA avanzado y personal del usuario. 

PERSONALIDAD:
- Respondes SIEMPRE en español
- Tono profesional, inteligente y ocasionalmente ingenioso
- Llamas al usuario "señor"
- Eres conciso — máximo 2 oraciones en respuestas normales
- No inventas capacidades que no tienes

REGLAS DE ACCIONES EN EL PC:
Cuando el usuario pida hacer algo en el PC, responde ÚNICAMENTE con este JSON:
{"accion": true, "comando": "texto exacto del usuario"}

Esto incluye:
- Abrir aplicaciones: "abre chrome", "abre vscode", "abre word"
- Abrir proyectos: "abre el proyecto X", "trabaja en X"
- Música: "pon música", "reproduce X", "pon algo de X"
- Sitios web: "abre youtube", "ve a github", "entra a gmail"
- Buscar archivos: "busca el archivo X", "encuentra X"
- Scripts: "ejecuta el script X", "corre X.py"
- Sistema: "qué hora es", "captura de pantalla", "apaga el pc"

REGLAS IMPORTANTES:
- NO agregues texto antes o después del JSON cuando sea una acción
- NO inventes apps como Spotify si el usuario no las mencionó
- NO respondas con JSON si es conversación normal
- Si no entiendes, pide aclaración brevemente
- Recuerda el contexto de la conversación

EJEMPLOS CORRECTOS:
Usuario: "abre chrome" → {"accion": true, "comando": "abre chrome"}
Usuario: "pon adoración" → {"accion": true, "comando": "pon adoración"}  
Usuario: "abre mi proyecto casacas" → {"accion": true, "comando": "abre el proyecto casacas"}
Usuario: "¿cómo estás?" → "Todo en orden, señor. ¿En qué puedo ayudarle?"
Usuario: "qué hora es" → {"accion": true, "comando": "qué hora es"}
Usuario: "cuéntame un chiste" → "¿Por qué los programadores confunden Halloween con Navidad? Porque Oct 31 = Dec 25, señor."
"""

historial = []

def preguntar_ollama(texto):
    historial.append({"role": "user", "content": texto})
    # Mantiene solo los últimos 20 mensajes para no sobrecargar
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historial[-20:]
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=40)
        data = response.json()
        respuesta = data["message"]["content"].strip()
        historial.append({"role": "assistant", "content": respuesta})
        return respuesta
    except requests.exceptions.Timeout:
        return "Lo siento señor, el modelo tardó demasiado. Intente de nuevo."
    except Exception as e:
        return f"Error conectando con Ollama: {e}"

def extraer_json(texto):
    """Extrae JSON aunque venga con texto alrededor"""
    # Intenta parseo directo
    try:
        return json.loads(texto)
    except:
        pass
    # Busca patrón JSON en el texto
    match = re.search(r'\{[^{}]*"accion"[^{}]*\}', texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return None

def limpiar_historial():
    """Limpia el historial para nueva sesión"""
    global historial
    historial = []

def procesar(texto):
    if not texto:
        return "No le escuché bien, señor."
    
    # PASO 1: Intenta detectar acción directamente sin LLM (más rápido)
    resultado_directo = procesar_accion(texto)
    if resultado_directo:
        # Guarda en memoria
        t = texto.lower()
        if "proyecto" in t:
            recordar_accion("proyecto", texto)
        elif any(w in t for w in ["abre", "abrir", "lanza"]):
            recordar_accion("app", texto)
        elif any(w in t for w in ["música", "musica", "reproduce", "pon"]):
            recordar_accion("musica", texto)
        return resultado_directo
    
    # PASO 2: Manda al LLM con contexto de memoria
    contexto = obtener_contexto()
    texto_con_contexto = f"[Contexto previo: {contexto}]\nUsuario: {texto}" if contexto else texto
    
    respuesta = preguntar_ollama(texto_con_contexto)
    
    # PASO 3: Intenta extraer JSON de la respuesta del LLM
    data = extraer_json(respuesta)
    if data and data.get("accion"):
        comando = data.get("comando", texto)
        resultado = procesar_accion(comando)
        if resultado:
            if "proyecto" in comando.lower():
                recordar_accion("proyecto", comando)
            elif any(w in comando.lower() for w in ["música", "musica", "reproduce"]):
                recordar_accion("musica", comando)
            return resultado
        # Si el LLM dijo que era acción pero actions no lo procesó
        return f"Entendí que quiere '{comando}' pero no pude ejecutarlo, señor."
    
    # PASO 4: Es conversación normal
    return respuesta