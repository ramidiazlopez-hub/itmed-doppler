import streamlit as st
from PIL import Image
import anthropic
from dotenv import load_dotenv
import os
import base64
import json
from datetime import datetime
from io import BytesIO

from plantillas import PLANTILLAS

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="ITMED Doppler", page_icon="🩺", layout="wide")
st.markdown(
    """
<style>
    html, body, .stApp {
        background-color: #f5f0eb !important;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    section[data-testid="stMain"],
    section[data-testid="stMain"] > div,
    .main,
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        background-color: #f5f0eb !important;
    }
    header[data-testid="stHeader"] {
        background-color: #BA7517 !important;
    }
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] [data-testid="stDecoration"] {
        color: #ffffff !important;
    }
    .main .block-container {
        padding-top: 1.25rem;
    }
    div.itmed-hero-header {
        background-color: #BA7517 !important;
        color: #ffffff !important;
        margin: -1.25rem -4rem 1rem -4rem !important;
        padding: 1.15rem calc(4rem + 1.25rem) 1.15rem calc(4rem + 1.25rem) !important;
        box-sizing: border-box;
    }
    div.itmed-hero-header h1 {
        background: transparent !important;
        background-color: transparent !important;
        color: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        font-size: clamp(1.25rem, 2.5vw, 1.75rem);
        font-weight: 700;
        line-height: 1.25;
    }
    div.itmed-hero-header .itmed-hero-sub {
        color: #ffffff !important;
        margin: 0.5rem 0 0 0 !important;
        padding: 0 !important;
        font-size: 1.05rem;
        font-weight: 500;
        opacity: 0.98;
    }
    .main h2 {
        color: #854F0B !important;
    }
    .stTextInput input,
    .stTextArea textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background-color: #f9f5f0 !important;
    }
    .stSelectbox [data-baseweb="select"] > div:first-child {
        background-color: #FAEEDA !important;
        border-color: #d4b896 !important;
    }
    .stSelectbox [data-baseweb="select"] > div:first-child p,
    .stSelectbox [data-baseweb="select"] > div:first-child span,
    .stSelectbox [data-baseweb="select"] > div:first-child div {
        color: #854F0B !important;
    }
    .stSelectbox [data-baseweb="select"] > div:first-child svg {
        fill: #854F0B !important;
    }
    .stFileUploader section[data-testid="stFileUploaderDropzone"] {
        background-color: #f9f5f0 !important;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stDownloadButton"] button {
        background-color: #BA7517 !important;
        color: #ffffff !important;
        border-color: #9a6314 !important;
    }
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #9a6314 !important;
        border-color: #854F0B !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:focus,
    div[data-testid="stDownloadButton"] button:focus {
        box-shadow: 0 0 0 2px #EF9F27 !important;
    }
    div[data-testid="element-container"][class*="itmed_informe_editor"],
    div[data-testid="element-container"][class*="itmed-informe-editor"] {
        border-left: 5px solid #EF9F27 !important;
        padding-left: 1rem !important;
        margin-bottom: 0.5rem !important;
        border-radius: 0 0.25rem 0.25rem 0 !important;
    }
    .main blockquote {
        border-left: 5px solid #EF9F27 !important;
        padding: 0.75rem 1rem !important;
        margin: 0 0 1rem 0 !important;
        background-color: #f9f5f0 !important;
        border-radius: 0 0.35rem 0.35rem 0 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="itmed-hero-header">
<h1>Sistema de Interpretación Eco Doppler Vascular</h1>
<p class="itmed-hero-sub">ITMED — Tecnología en Salud</p>
</div>
""",
    unsafe_allow_html=True,
)
st.divider()

MEDICO_NOMBRE = "Dr. Diaz Lopez Ramiro"
MEDICO_MATRICULA = "MP 21989 REG ESP 540188"
INSTITUCION = "ITMED — Tecnología en Salud"

def imagen_a_base64(imagen_pil):
    buffer = BytesIO()
    imagen_pil.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def guardar_caso(paciente, tipo_estudio, fecha, informe_ia, informe_final):
    caso = {
        "fecha_sistema": datetime.now().isoformat(),
        "paciente": paciente,
        "tipo_estudio": tipo_estudio,
        "fecha_estudio": str(fecha),
        "informe_ia": informe_ia,
        "informe_final": informe_final,
        "modificado": informe_ia.strip() != informe_final.strip()
    }
    archivo_db = "casos.json"
    if os.path.exists(archivo_db):
        with open(archivo_db, "r", encoding="utf-8") as f:
            datos = json.load(f)
    else:
        datos = []
    datos.append(caso)
    with open(archivo_db, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return len(datos)

def analizar_doppler(imagenes_b64, tipo_estudio, observaciones, valores_adicionales, plantilla_base):
    seccion_adicional = ""
    if valores_adicionales.strip():
        seccion_adicional = "El medico informante provee ademas estos valores medidos manualmente:\n" + valores_adicionales + "\n\n"

    if plantilla_base.strip():
        prompt = (
            "Sos un medico especialista en ecografia Doppler vascular con amplia experiencia clinica.\n"
            "Analizas imagenes de un estudio de " + tipo_estudio + ".\n\n"
            + seccion_adicional +
            "Observaciones clinicas: " + (observaciones if observaciones else "No especificadas") + "\n\n"
            "Debés redactar el informe final usando EXCLUSIVAMENTE la siguiente plantilla como estructura.\n"
            "Reglas obligatorias:\n"
            "- Conservá el formato de la plantilla tal cual: mismos titulos, orden de lineas, saltos de linea y convenciones (por ejemplo PS/ED/RI, guiones bajos donde correspondan).\n"
            "- Completá cada campo, valor numerico y descripcion con los datos que extraigas de las imagenes del estudio, de las observaciones clinicas y de los valores adicionales aportados.\n"
            "- Donde la plantilla ofrece alternativas entre corchetes [opcion A / opcion B], elegí la que corresponda segun los hallazgos.\n"
            "- Si un dato no es visible o no se puede inferir con razonable certeza, indicá de forma breve y profesional que no fue posible determinarlo o que no es evaluable en este estudio, sin inventar cifras.\n"
            "- No agregues secciones ajenas a la plantilla (no incluyas apartados extra como TECNICA o HALLAZGOS por fuera de la estructura dada).\n"
            "- Mantené la redaccion en espanol medico claro y conciso.\n\n"
            "PLANTILLA BASE (replicá esta estructura al pie de la letra, sustituyendo placeholders y completando mediciones):\n\n"
            + plantilla_base.strip()
        )
    else:
        prompt = (
            "Sos un medico especialista en ecografia Doppler vascular con amplia experiencia clinica.\n"
            "Analizas imagenes de un estudio de " + tipo_estudio + ".\n\n"
            + seccion_adicional +
            "Observaciones clinicas: " + (observaciones if observaciones else "No especificadas") + "\n\n"
            "Genera un informe estructurado completo con estas secciones:\n\n"
            "TECNICA:\n"
            "Describe brevemente el metodo utilizado.\n\n"
            "HALLAZGOS:\n"
            "Para cada vaso identificado indica en tabla:\n"
            "- Nombre del vaso\n"
            "- PS (cm/s), ED (cm/s), RI, S/D\n"
            "- Patron espectral: indica claramente si es MONOFASICO, BIFASICO o TRIFASICO\n"
            "- Resistencia vascular: indica si es ALTA RESISTENCIA o BAJA RESISTENCIA con justificacion\n\n"
            "INTERPRETACION HEMODINAMICA:\n"
            "Para cada vaso explica el significado clinico. Incluye obligatoriamente:\n"
            "- Clasificacion del patron de flujo (monofasico/bifasico/trifasico)\n"
            "- Clasificacion de resistencia (alta/baja) con valor de RI como referencia\n"
            "- Si los valores son normales o patologicos y por que\n"
            "- Si hay signos de estenosis, obstruccion o alteracion hemodinamica significativa\n\n"
            "CONCLUSION:\n"
            "Diagnostico principal claro y conciso. Recomendaciones si corresponde."
        )

    contenido = []
    for b64 in imagenes_b64:
        contenido.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64
            }
        })
    contenido.append({"type": "text", "text": prompt})

    respuesta = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": contenido}]
    )
    return respuesta.content[0].text

st.header("Datos del estudio")
col1, col2 = st.columns(2)

with col1:
    paciente = st.text_input("Nombre del paciente")
    tipo_estudio = st.selectbox(
        "Tipo de estudio",
        [
            "Seleccionar...",
            "Doppler vasos de cuello",
            "Doppler arterial miembros inferiores",
            "Doppler venoso miembros inferiores",
            "Doppler aorta abdominal",
            "Doppler arterial miembros superiores"
        ]
    )
    if tipo_estudio in PLANTILLAS:
        with st.expander("Ver plantilla base"):
            st.text(PLANTILLAS[tipo_estudio])

with col2:
    fecha = st.date_input("Fecha del estudio")
    observaciones = st.text_area("Observaciones clinicas")

st.divider()
st.header("Valores adicionales")
st.caption("Ingresa aqui los valores de vasos que no esten marcados en las imagenes")
valores_adicionales = st.text_area(
    "Ejemplo:  AVD: PS 45 cm/s, ED 12 cm/s, RI 0.73 | ACCD: PS 67 cm/s, ED 18 cm/s, RI 0.68",
    height=80
)

st.divider()
st.header("Cargar imagenes")
archivos = st.file_uploader(
    "Selecciona las imagenes del estudio",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if archivos:
    cols = st.columns(min(len(archivos), 3))
    for i, img_file in enumerate(archivos):
        with cols[i % 3]:
            imagen = Image.open(img_file)
            st.image(imagen, caption="Imagen " + str(i+1), width=400)
    st.success(str(len(archivos)) + " imagen(es) cargada(s)")

st.divider()

if st.button("Analizar con IA", type="primary", use_container_width=True):
    if not archivos:
        st.error("Primero carga al menos una imagen")
    elif tipo_estudio == "Seleccionar...":
        st.error("Selecciona el tipo de estudio")
    else:
        with st.spinner("Analizando imagenes... esto tarda unos 20 segundos"):
            imagenes_b64 = []
            for img_file in archivos:
                img = Image.open(img_file).convert("RGB")
                imagenes_b64.append(imagen_a_base64(img))
            informe = analizar_doppler(
                imagenes_b64,
                tipo_estudio,
                observaciones,
                valores_adicionales,
                PLANTILLAS.get(tipo_estudio, ""),
            )
            st.session_state["informe_ia"] = informe
            st.session_state["paciente"] = paciente
            st.session_state["tipo_estudio"] = tipo_estudio
            st.session_state["fecha"] = fecha

if "informe_ia" in st.session_state:
    st.divider()
    st.header("Informe generado por IA")
    st.caption("Revisa y edita antes de guardar")

    informe_editado = st.text_area(
        "Edita el informe:",
        value=st.session_state["informe_ia"],
        height=450,
        key="itmed_informe_editor",
    )

    firma = (
        "\n\n---\n\n"
        "**DR. DIAZ LOPEZ RAMIRO**  \n"
        "MP 21989 REG ESP 540188  \n"
        "Fecha de emisión: " + datetime.now().strftime("%d/%m/%Y %H:%M") + "  \n"
        "ITMED — Tecnología en Salud"
    )

    informe_con_firma = informe_editado + firma

    col3, col4 = st.columns(2)

    with col3:
        if st.button("Guardar caso en base de datos", type="primary"):
            total = guardar_caso(
                st.session_state.get("paciente", ""),
                st.session_state.get("tipo_estudio", ""),
                st.session_state.get("fecha", ""),
                st.session_state["informe_ia"],
                informe_editado
            )
            st.success("Caso guardado. Total acumulado: " + str(total) + " casos")

    with col4:
        st.download_button(
            label="Descargar informe con firma",
            data=informe_con_firma,
            file_name="informe_" + st.session_state.get("paciente", "paciente") + "_" + str(st.session_state.get("fecha", "")) + ".txt",
            mime="text/plain"
        )

    st.divider()
    if st.button("Nuevo estudio", use_container_width=True):
        for key in ["informe_ia", "paciente", "tipo_estudio", "fecha"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.subheader("Vista previa con firma")
    st.markdown(
        "\n".join(
            ("> " + _ln if _ln.strip() else ">")
            for _ln in informe_con_firma.replace("\n", "  \n").split("\n")
        )
    )