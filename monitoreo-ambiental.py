import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Carpeta Excel
RUTA_EXCEL = r"C:\Users\xosec\Documents\ComputerScience\DataScience\projects\temp-hum"

# === Cargar variables de entorno ===
load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# === CONFIGURACIÓN POR ÁREA ===
AREAS_CONFIG = {
    "Microbiología clínica": {
        "temp_a": 0.97, "temp_b": 0.6,
        "hum_a": 1.03, "hum_b": -2,
        "temp_min": 20, "temp_max": 25,
        "hum_min": 35, "hum_max": 60,
        "email": "laboratorio.calidad@choco.gov.co"
    },
    "Fisicoquímico de aguas": {
        "temp_a": 0.99, "temp_b": 0.4,
        "hum_a": 1.01, "hum_b": -1,
        "temp_min": 18, "temp_max": 24,
        "hum_min": 30, "hum_max": 55,
        "email": "laboratorio.calidad@choco.gov.co"
    },
    "Cepario": {
        "temp_a": 0.98, "temp_b": 0.5,
        "hum_a": 1.02, "hum_b": -1.5,
        "temp_min": 21, "temp_max": 26,
        "hum_min": 40, "hum_max": 65,
        "email": "laboratorio.calidad@choco.gov.co"
    },
     "Entomología": {
        "temp_a": 0.98, "temp_b": 0.5,
        "hum_a": 1.02, "hum_b": -1.5,
        "temp_min": 21, "temp_max": 26,
        "hum_min": 40, "hum_max": 65,
        "email": "laboratorio.calidad@choco.gov.co"
    }    
}

# === FUNCIONES ===
def corregir(valor, a, b):
    return a * valor + b

def enviar_alerta(area, fecha, turno, temp_corr, hum_corr, limites, destinatario, responsable):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Alerta: condiciones fuera de rango - {fecha} ({turno}) - {area}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = destinatario

    msg.set_content(f"""
    Alerta por condiciones fuera de rango:

    Área: {area}
    Fecha: {fecha}
    Responsable: {responsable}
    Turno: {turno}
    Temperatura corregida: {temp_corr:.2f} °C
    Humedad corregida: {hum_corr:.2f} %

    Límites esperados:
    Temperatura: {limites['temp_min']} - {limites['temp_max']} °C
    Humedad: {limites['hum_min']} - {limites['hum_max']} %
    """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"❌ Error al enviar correo: {e}")

def guardar_datos(area, datos):
    nombre_archivo = f"{area.lower().replace(' ', '_')}.xlsx"
    ruta_archivo = os.path.join(RUTA_EXCEL, nombre_archivo)

    try:
        if os.path.exists(ruta_archivo):
            df_existente = pd.read_excel(ruta_archivo)
            df = pd.concat([df_existente, pd.DataFrame([datos])], ignore_index=True)
        else:
            df = pd.DataFrame([datos])

        df.to_excel(ruta_archivo, index=False)
        st.success(f"✅ Datos guardados en: `{ruta_archivo}`")
    except Exception as e:
        st.error(f"❌ Error al guardar datos en Excel: {e}")


# === INTERFAZ STREAMLIT ===
st.set_page_config(page_title="Monitoreo de Condiciones Ambientales", page_icon="🌡️")
st.title("🌡️ Monitoreo de Temperatura y Humedad - Laboratorio de Salud Pública Departamental del Chocó")

# Selección de área
area = st.selectbox("Selecciona el área del laboratorio", list(AREAS_CONFIG.keys()))
params = AREAS_CONFIG[area]

# Mostrar parámetros actuales
with st.expander("🔧 Parámetros del área seleccionada"):
    st.write(f"**Corrección de Temperatura**: y = {params['temp_a']} * x + {params['temp_b']}")
    st.write(f"**Corrección de Humedad**: y = {params['hum_a']} * x + {params['hum_b']}")
    st.write(f"**Límites Temperatura**: {params['temp_min']} - {params['temp_max']} °C")
    st.write(f"**Límites Humedad**: {params['hum_min']} - {params['hum_max']} %")
    st.write(f"**Correo de alerta**: {params['email']}")

# Formulario de ingreso
with st.form("formulario"):
    nombre_usuario = st.text_input("Nombre del responsable", max_chars=50)
    turno = st.selectbox("Turno", ["Mañana", "Tarde"])
    hora = st.time_input("Hora del monitoreo", value=datetime.now().time())
    temp = st.number_input("Temperatura medida (°C)", format="%.2f")
    hum = st.number_input("Humedad relativa medida (%)", format="%.2f")
    submitted = st.form_submit_button("Guardar")

if submitted:
    fecha = datetime.now().strftime("%Y-%m-%d")

    temp_corr = corregir(temp, params["temp_a"], params["temp_b"])
    hum_corr = corregir(hum, params["hum_a"], params["hum_b"])

    datos = {
    "Fecha": fecha,
    "Hora": hora.strftime("%H:%M"),
    "Área": area,
    "Turno": turno,
    "Responsable": nombre_usuario,
    "Temp Original (°C)": temp,
    "Temp Corregida (°C)": temp_corr,
    "Humedad Original (%)": hum,
    "Humedad Corregida (%)": hum_corr,
}

    guardar_datos(area, datos)

    fuera_temp = not (params["temp_min"] <= temp_corr <= params["temp_max"])
    fuera_hum = not (params["hum_min"] <= hum_corr <= params["hum_max"])

    if fuera_temp or fuera_hum:
        enviar_alerta(area, fecha, turno, temp_corr, hum_corr, params, params["email"], nombre_usuario)
        st.warning("⚠️ Se ha enviado una alerta por valores fuera de rango.")

    st.success("✅ Datos guardados correctamente.")

    # Ejecutar en prompt de anaconda como
    # streamlit run C:\Users\xosec\Documents\ComputerScience\DataScience\projects\temp-hum\monitoreo-ambiental.py
