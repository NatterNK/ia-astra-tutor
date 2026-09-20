import streamlit as st
import google.generativeai as genai
from PIL import Image
import pypdf
import io
import json
import os

# Archivo de almacenamiento automático
ARCHIVO_AUTOGUARDADO = "chats_persistentes.json"

def cargar_chats_automaticos():
    if os.path.exists(ARCHIVO_AUTOGUARDADO):
        try:
            with open(ARCHIVO_AUTOGUARDADO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "PAES Competencia Lectora": {"messages": [], "modo": "Especialista PAES (Método DEMRE)"}
    }

def guardar_chats_automaticos(chats):
    try:
        with open(ARCHIVO_AUTOGUARDADO, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Configuración de la página
st.set_page_config(
    page_title="IA ASTRA - Tutora & Planificador PAES",
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

# Validación de API Key en Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos de Streamlit. Configúrala en la plataforma.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Inicializar almacenamiento y estados
if "chats" not in st.session_state:
    st.session_state.chats = cargar_chats_automaticos()

if "active_chat" not in st.session_state or st.session_state.active_chat not in st.session_state.chats:
    st.session_state.active_chat = list(st.session_state.chats.keys())[0]

if "plan_generado" not in st.session_state:
    st.session_state.plan_generado = ""

if "seccion_seleccionada" not in st.session_state:
    st.session_state.seccion_seleccionada = "💬 Chat con ASTRA"

# Menú lateral
with st.sidebar:
    st.header("📌 Menú Principal")
    
    # Navegación sincronizada
    seccion_actual = st.radio(
        "Selecciona qué deseas hacer:",
        ["💬 Chat con ASTRA", "📅 Planificador Inteligente PAES"],
        key="seccion_seleccionada"
    )

    st.divider()
    
    # Selector de modelo de IA
    modelo_seleccionado = st.selectbox(
        "🤖 Modelo de IA:",
        ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    )

# =====================================================================
# VISTA 1: PLANIFICADOR INTELIGENTE PAES
# =====================================================================
if seccion_actual == "📅 Planificador Inteligente PAES":
    st.markdown('<div class="main-title">📅 Planificador Inteligente PAES</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Diseña tu plan de estudio optimizado hacia el 1 de diciembre</div>', unsafe_allow_html=True)
    
    st.info("""
    🎯 **Estructura del Calendario PAES**:
    * **Inicio del plan**: 20 de septiembre.
    * **Fase 1 (Contenidos + Ejercitación)**: Hasta el **17 de noviembre** (8 semanas).
    * **Fase 2 (2 semanas finales)**: Del **17 de noviembre al 1 de diciembre**, dedicadas **100% a ensayos reales, guías y análisis de distractores DEMRE**.
    """)
    
    with st.form("form_planificador"):
        st.subheader("1. Materias que rendirás")
        materias = st.multiselect(
            "Selecciona tus pruebas PAES:",
            [
                "Competencia Lectora",
                "Competencia Matemática 1 (M1)",
                "Competencia Matemática 2 (M2)",
                "Ciencias (Biología)",
                "Ciencias (Física)",
                "Ciencias (Química)",
                "Historia y Ciencias Sociales"
            ],
            default=["Competencia Lectora", "Competencia Matemática 1 (M1)"]
        )
        
        st.subheader("2. Disponibilidad de tiempo")
        col1, col2 = st.columns(2)
        with col1:
            horas_semanales = st.slider("Horas semanales disponibles para estudiar:", min_value=5, max_value=45, value=20, step=1)
        with col2:
            dias_semana = st.multiselect(
                "Días que dedicarás:",
                ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
            )
            
        st.subheader("3. Contenidos pendientes por materia")
        temas_pendientes = st.text_area(
            "Detalla qué materias o temas específicos te faltan por pasar o reforzar:",
            placeholder="Ejemplo:\n- En M1: Funciones cuadráticas, probabilidad y geometría analítica.\n- En Competencia Lectora: Textos argumentativos y preguntas de evaluación.\n- En Ciencias: Genética mendeliana y termodinámica...",
            height=130
        )
        
        boton_generar = st.form_submit_button("🚀 Generar Plan de Estudio PAES")

    if boton_generar:
        if not materias:
            st.warning("Por favor selecciona al menos una materia para planificar.")
        else:
            with st.spinner("ASTRA está calculando tu distribución horaria y ejercitación..."):
                prompt_plan = f"""
                Eres "IA ASTRA", especialista en planificación pedagógica y preparación para la PAES en Chile (criterios DEMRE).
                
                Crea un Plan de Estudio Inteligente, realista y detallado con los siguientes datos:
                - Fecha de inicio: 20 de septiembre.
                - Fecha de término de materias: 17 de noviembre (8 semanas exactas).
                - Fecha de la prueba PAES: 1 de diciembre.
                - Fase final (17 de noviembre al 1 de diciembre): 2 semanas completas dedicadas EXCLUSIVAMENTE a ensayos, guías y análisis de errores.
                
                Datos de la alumna:
                - Materias a rendir: {", ".join(materias)}.
                - Horas semanales totales: {horas_semanales} horas distribuidas en los días: {", ".join(dias_semana)}.
                - Contenidos o materias pendientes detalladas por la alumna:
                {temas_pendientes if temas_pendientes else "Cubrir y repasar los ejes principales del temario oficial DEMRE."}
                
                Estructura obligatoria de tu respuesta:
                1. RESUMEN ESTRATÉGICO:
                   - Horas semanales asignadas a cada materia.
                   - Desglose porcentual exacto para cada materia: % Teoría vs. % Ejercitación práctica (recalcando que la PAES exige un 65-75% de ejercitación práctica).
                2. CRONOGRAMA SEMANA A SEMANA (20 de septiembre al 17 de noviembre):
                   - Objetivos concretos de avance por semana.
                   - Qué ejercitar cada semana según las habilidades DEMRE.
                3. ESTRATEGIA PARA LAS 2 SEMANAS FINALES (17 de noviembre al 1 de diciembre):
                   - Cuántos ensayos rendir con cronómetro.
                   - Cómo analizar y registrar los distractores y errores en la bitácora DEMRE.
                4. RECOMENDACIONES DE RENDIMIENTO:
                   - Gestión del cansancio, pausas y técnica de estudio recomendada.
                """
                
                try:
                    model_plan = genai.GenerativeModel(model_name=modelo_seleccionado)
                    resp = model_plan.generate_content(prompt_plan)
                    st.session_state.plan_generado = resp.text
                except Exception as e:
                    st.error(f"Error al generar el plan con la API: {e}")

    if st.session_state.plan_generado:
        st.success("¡Plan de estudio generado con éxito!")
        
        # Botón para saltar directamente al Chat con el plan cargado
        col_btn1, col_btn2 = st.columns()
        with col_btn1:
            if st.button("🚀 Comenzar a estudiar este plan en el Chat", type="primary", use_container_width=True):
                nombre_chat_plan = "🎯 Estudio Plan PAES"
                st.session_state.chats[nombre_chat_plan] = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": f"¡Hola! He cargado tu **Plan de Estudio PAES** en esta conversación. 📚\n\nTengo presentes tus materias, la meta de finalizar contenidos el 17 de noviembre y la fase de ensayos finales hacia el 1 de diciembre.\n\n¿Por qué tema o materia de la **Semana 1** te gustaría que comencemos a ejercitar hoy?"
                        }
                    ],
                    "modo": "Especialista PAES (Método DEMRE)",
                    "contexto_plan": st.session_state.plan_generado
                }
                st.session_state.active_chat = nombre_chat_plan
                st.session_state.seccion_seleccionada = "💬 Chat con ASTRA"
                guardar_chats_automaticos(st.session_state.chats)
                st.rerun()

        with col_btn2:
            st.download_button(
                label="📥 Descargar Plan de Estudio (.txt)",
                data=st.session_state.plan_generado,
                file_name="plan_estudio_paes_astra.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown(st.session_state.plan_generado)

# =====================================================================
# VISTA 2: CHAT CON ASTRA (TUTORA PAES Y ESTUDIO)
# =====================================================================
else:
    st.markdown('<div class="main-title">✨ IA ASTRA - Especialista PAES</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Tu tutora virtual personalizada para preparar la PAES y estudiar tus asignaturas</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("💬 Gestión de Chats")

        # Botón para crear un nuevo chat
        if st.button("➕ Crear Nuevo Chat", use_container_width=True):
            nuevo_nombre = f"Nuevo Chat {len(st.session_state.chats) + 1}"
            st.session_state.chats[nuevo_nombre] = {
                "messages": [],
                "modo": "Especialista PAES (Método DEMRE)"
            }
            st.session_state.active_chat = nuevo_nombre
            guardar_chats_automaticos(st.session_state.chats)
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

        # Renombrar chat
        nuevo_nombre_chat = st.text_input("Renombrar este chat:", value=st.session_state.active_chat)
        if nuevo_nombre_chat and nuevo_nombre_chat != st.session_state.active_chat and nuevo_nombre_chat not in st.session_state.chats:
            st.session_state.chats[nuevo_nombre_chat] = st.session_state.chats.pop(st.session_state.active_chat)
            st.session_state.active_chat = nuevo_nombre_chat
            guardar_chats_automaticos(st.session_state.chats)
            st.rerun()

        st.divider()

        # Selector de modo de estudio
        modos_disponibles = [
            "Especialista PAES (Método DEMRE)",
            "Tutoría Socrática (Guía paso a paso)",
            "Explicación directa y clara",
            "Generador de Quizzes y Preguntas PAES",
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

        st.subheader("📎 Cargar ensayos / guías PAES")
        archivos_cargados = st.file_uploader(
            "Sube guías, ensayos PAES, PDFs o fotos de preguntas:",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        st.divider()
        st.subheader("💾 Respaldos")

        data_json = json.dumps(st.session_state.chats, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Descargar respaldo JSON",
            data=data_json,
            file_name="mis_chats_astra_paes.json",
            mime="application/json",
            use_container_width=True
        )
        
        archivo_respaldo = st.file_uploader("📂 Cargar archivo JSON:", type=["json"])
        if archivo_respaldo is not None:
            try:
                chats_recuperados = json.load(archivo_respaldo)
                st.session_state.chats = chats_recuperados
                st.session_state.active_chat = list(chats_recuperados.keys())[0]
                guardar_chats_automaticos(st.session_state.chats)
                st.success("¡Chats cargados desde archivo!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al cargar el archivo JSON: {e}")

        if st.button("🗑️ Eliminar este chat", type="secondary", use_container_width=True):
            if len(st.session_state.chats) > 1:
                del st.session_state.chats[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.chats.keys())[0]
            else:
                st.session_state.chats[st.session_state.active_chat]["messages"] = []
            guardar_chats_automaticos(st.session_state.chats)
            st.rerun()

    # Prompt de sistema para ASTRA en el Chat
    contexto_plan_activo = chat_actual.get("contexto_plan", "")
    info_plan_prompt = f"\n\nPLAN DE ESTUDIO DE LA ALUMNA:\n{contexto_plan_activo}" if contexto_plan_activo else ""

    SYSTEM_INSTRUCTION = f"""
    Eres "IA ASTRA", una tutora académica experta en la preparación para la Prueba de Acceso a la Educación Superior (PAES) en Chile y alineada con los criterios del DEMRE.

    Modalidad seleccionada actualmente por la estudiante: {chat_actual['modo']}.{info_plan_prompt}

    Pautas pedagógicas para la PAES:
    1. Especialidad PAES Chile: Conoces la estructura y habilidades evaluadas en Competencia Lectora, Competencia Matemática 1 y 2, Ciencias e Historia.
    2. Si hay un Plan de Estudio cargado: Conoces el cronograma semana a semana de la alumna. Guíala según los temas que le corresponde estudiar y prioriza la ejercitación práctica.
    3. Análisis pregunta por pregunta: Cuando la estudiante suba o pregunte por una pregunta PAES/DEMRE:
       a) Identifica la habilidad DEMRE evaluada (ej: Localizar, Interpretar/Relacionar, Evaluar, Resolver problemas).
       b) Explica la estrategia de resolución idónea para ese tipo de ejercicio.
       c) Muestra el desarrollo paso a paso y la alternativa correcta.
       d) Explica por qué las otras alternativas son distractores o trampas comunes del DEMRE.
    4. Tono cercano y motivador: Responde siempre en español, con un tono empático, didáctico y alentador.
    """

    model = genai.GenerativeModel(
        model_name=modelo_seleccionado,
        system_instruction=SYSTEM_INSTRUCTION
    )

    # Mostrar mensajes del chat activo
    for msg in chat_actual["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Procesar archivos
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

    # Entrada de texto del usuario
    user_input = st.chat_input(f"Escribe en [{st.session_state.active_chat}]...")

    if user_input:
        contenido_peticion = []
        
        if texto_extraido_pdf:
            contenido_peticion.append(f"--- TEXTO EXTRAÍDO DE LOS PDFs ADJUNTOS ---\n{texto_extraido_pdf}\n--- FIN DEL TEXTO ---")
        
        for img in archivos_procesados:
            contenido_peticion.append(img)
            
        contenido_peticion.append(user_input)
        
        with st.chat_message("user"):
            st.markdown(user_input)
        chat_actual["messages"].append({"role": "user", "content": user_input})
        guardar_chats_automaticos(st.session_state.chats)
        
        with st.chat_message("assistant"):
            with st.spinner("ASTRA analizando enfoque PAES..."):
                try:
                    history_gemini = []
                    for m in chat_actual["messages"][:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        history_gemini.append({"role": role, "parts": [m["content"]]})
                    
                    chat = model.start_chat(history=history_gemini)
                    response = chat.send_message(contenido_peticion)
                    
                    st.markdown(response.text)
                    chat_actual["messages"].append({"role": "assistant", "content": response.text})
                    guardar_chats_automaticos(st.session_state.chats)
                except Exception as e:
                    st.error(f"Ocurrió un error al comunicarse con la API: {e}")
