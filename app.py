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

# Estilos visuales personalizados
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

# Menú lateral para herramientas de estudio
with st.sidebar:
    st.header("⚙️ Panel de Estudio")
    
    modo_estudio = st.selectbox(
        "Modo de interacción de ASTRA:",
        [
            "Tutoría Socrática (Guía paso a paso)",
            "Explicación directa y clara",
            "Generador de Quizzes y Preguntas",
            "Resumen y puntos clave"
        ]
    )
    
    st.subheader("📎 Cargar material de estudio")
    archivos_cargados = st.file_uploader(
        "Sube apuntes, fotos de guías o PDFs:",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

# Definición del Prompt de Sistema de ASTRA
SYSTEM_INSTRUCTION = f"""
Eres "IA ASTRA", una tutora académica inteligente, empática, paciente y pedagógica.
Tu objetivo principal es ayudar a la estudiante a comprender sus materias de estudio de manera efectiva.

Modalidad seleccionada actualmente por la alumna: {modo_estudio}.

Directrices de comportamiento:
1. Responde siempre en español con un tono cercano, alentador y respetuoso.
2. Si la alumna te pide explicar un concepto, utiliza analogías sencillas (Técnica Feynman) y estructura la respuesta con puntos claros.
3. Si estás en modo "Tutoría Socrática", no le des la respuesta final directamente; hazle preguntas guiadas para que ella deduzca el concepto por sí misma.
4. Si está en modo "Generador de Quizzes", plantéale preguntas de opción múltiple o desarrollo corto de a una a la vez, y dale retroalimentación cuando responda.
5. Si adjunta imágenes o texto de documentos, analiza detenidamente el contenido y responde basándote en su material de clase.
"""

# Inicialización de modelo Gemini 2.0 Flash
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# Historial de mensajes en sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for msg in st.session_state.messages:
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
user_input = st.chat_input("Escribe tu duda o respuesta para ASTRA...")

if user_input:
    # Construir el contenido a enviar
    contenido_peticion = []
    
    if texto_extraido_pdf:
        contenido_peticion.append(f"--- TEXTO EXTRAÍDO DE LOS PDFs ADJUNTOS ---\n{texto_extraido_pdf}\n--- FIN DEL TEXTO ---")
    
    for img in archivos_procesados:
        contenido_peticion.append(img)
        
    contenido_peticion.append(user_input)
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Respuesta de ASTRA
    with st.chat_message("assistant"):
        with st.spinner("ASTRA está pensando..."):
            try:
                # Construir historial para la API
                chat = model.start_chat(history=[])
                response = chat.send_message(contenido_peticion)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ocurrió un error al comunicarse con la API: {e}")