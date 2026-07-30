import streamlit as st
import google.generativeai as genai
from PIL import Image
import pypdf
import io

# Configuración de la página
st.set_page_config(
    page_title="IA ASTRA - Tu Tutora de Estudio",
    page_icon="✨",
    layout="centered"
)

# Estilos visuales
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #4A90E2;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #6C757D;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✨ IA ASTRA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Tu asistenta virtual personalizada para estudiar y repasar</div>', unsafe_allow_html=True)

# Validación de API Key en Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos de Streamlit. Configúrala en la plataforma.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Inicialización del almacenamiento de múltiples chats
if "chats" not in st.session_state:
    st.session_state.chats = {
        "Chat General": {"messages": [], "modo": "Tutoría Socrática (Guía paso a paso)"}
    }

if "active_chat" not in st.session_state or st.session_state.active_chat not in st.session_state.chats:
    st.session_state.active_chat = "Chat General"

# Menú lateral para gestión de múltiples chats y herramientas
with st.sidebar:
    st.header("⚙️ Panel de Estudio")
    
    # Selector de modelo de IA
    modelo_seleccionado = st.selectbox(
        "🤖 Modelo de IA:",
        ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.5-flash", "gemini-pro"]
    )

    st.divider()

    # Botón para crear un nuevo chat
    if st.button("➕ Crear Nuevo Chat", use_container_width=True):
        nuevo_nombre = f"Nuevo Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[nuevo_nombre] = {
            "messages": [],
            "modo": "Tutoría Socrática (Guía paso a paso)"
        }
        st.session_state.active_chat = nuevo_nombre
        st.rerun()

    # Selector de chat activo
    lista_chats = list(st.session_state.chats.keys())
    indice_activo = lista_chats.index(st.session_state.active_chat) if st.session_state.active_chat in lista_chats else 0
    
    chat_seleccionado = st.selectbox(
        "Mis Chats / Materias:",
        lista_chats,
        index=indice_activo
    )
    st.session_state.active_chat = chat_seleccionado
    chat_actual = st.session_state.chats[st.session_state.active_chat]

    # Campo para renombrar el chat activo
    nuevo_nombre_chat = st.text_input("Renombrar este chat:", value=st.session_state.active_chat)
    if nuevo_nombre_chat and nuevo_nombre_chat != st.session_state.active_chat and nuevo_nombre_chat not in st.session_state.chats:
        st.session_state.chats[nuevo_nombre_chat] = st.session_state.chats.pop(st.session_state.active_chat)
        st.session_state.active_chat = nuevo_nombre_chat
        st.rerun()

    st.divider()

    # Selector de modo de estudio
    modos_disponibles = [
        "Tutoría Socrática (Guía paso a paso)",
        "Explicación directa y clara",
        "Generador de Quizzes y Preguntas",
        "Resumen y puntos clave"
    ]
    modo_actual = chat_actual.get("modo", modos_disponibles[0])
    idx_modo = modos_disponibles.index(modo_actual) if modo_actual in modos_disponibles else 0
    
    modo_estudio = st.selectbox(
        "Modo de interacción de ASTRA:",
        modos_disponibles,
        index=idx_modo
    )
    chat_actual["modo"] = modo_estudio

    st.subheader("📎 Cargar material de estudio")
    archivos_cargados = st.file_uploader(
        "Sube apuntes, fotos de guías o PDFs:",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if st.button("🗑️ Eliminar este chat", type="secondary", use_container_width=True):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.active_chat]
            st.session_state.active_chat = list(st.session_state.chats.keys())[0]
            st.rerun()
        else:
            st.session_state.chats[st.session_state.active_chat]["messages"] = []
            st.rerun()

# Definición del Prompt de Sistema de ASTRA
SYSTEM_INSTRUCTION = f"""
Eres "IA ASTRA", una tutora académica inteligente, empática, paciente y pedagógica.
Tu objetivo principal es ayudar a la estudiante a comprender sus materias de estudio de manera efectiva.

Modalidad seleccionada actualmente por la alumna en esta sesión: {chat_actual['modo']}.

Directrices de comportamiento:
1. Responde siempre en español con un tono cercano, alentador y respetuoso.
2. Si la alumna te pide explicar un concepto, utiliza analogías sencillas (Técnica Feynman) y estructura la respuesta con puntos claros.
3. Si estás en modo "Tutoría Socrática", no le des la respuesta final directamente; hazle preguntas guiadas para que ella deduzca el concepto por sí misma.
4. Si está en modo "Generador de Quizzes", plantéale preguntas de opción múltiple o desarrollo corto de a una a la vez, y dale retroalimentación cuando responda.
5. Si adjunta imágenes o texto de documentos, analiza detenidamente el contenido y responde basándote en su material de clase.
"""

# Inicialización con el modelo seleccionado en el menú
model = genai.GenerativeModel(
    model_name=modelo_seleccionado,
    system_instruction=SYSTEM_INSTRUCTION
)

# Mostrar mensajes del chat activo
for msg in chat_actual["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Procesamiento de archivos adjuntos
archivos_procesados = []
texto_extraido_pdf = ""

if archivos_cargados:
    for archivo in archivos_cargados:
        if archivo.type == "application/pdf":
            try:
                pdf_reader = pypdf.PdfReader(io.BytesIO(archivo.read()))
                for page in pdf_reader.pages:
                    texto_extraido_pdf += page.extract_text() + "\n"
            except Exception as e:
                st.error(f"Error al leer el PDF {archivo.name}: {e}")
        elif archivo.type in ["image/png", "image/jpg", "image/jpeg"]:
            try:
                img = Image.open(archivo)
                archivos_procesados.append(img)
            except Exception as e:
                st.error(f"Error al procesar la imagen {archivo.name}: {e}")

# Entrada de usuario
user_input = st.chat_input(f"Escribe en [{st.session_state.active_chat}]...")

if user_input:
    # Construir contenido
    contenido_peticion = []
    
    if texto_extraido_pdf:
        contenido_peticion.append(f"--- TEXTO EXTRAÍDO DE LOS PDFs ADJUNTOS ---\n{texto_extraido_pdf}\n--- FIN DEL TEXTO ---")
    
    for img in archivos_procesados:
        contenido_peticion.append(img)
        
    contenido_peticion.append(user_input)
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(user_input)
    chat_actual["messages"].append({"role": "user", "content": user_input})
    
    # Respuesta de ASTRA
    with st.chat_message("assistant"):
        with st.spinner("ASTRA está pensando..."):
            try:
                # Formatear historial existente para Gemini API
                history_gemini = []
                for m in chat_actual["messages"][:-1]:
                    role = "user" if m["role"] == "user" else "model"
                    history_gemini.append({"role": role, "parts": [m["content"]]})
                
                chat = model.start_chat(history=history_gemini)
                response = chat.send_message(contenido_peticion)
                
                st.markdown(response.text)
                chat_actual["messages"].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ocurrió un error al comunicarse con la API: {e}")
