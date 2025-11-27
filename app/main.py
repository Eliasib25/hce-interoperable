from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from . import fhir_client
from io import BytesIO 
from datetime import timedelta, date, datetime
from xhtml2pdf import pisa# Para la fecha en el PDF

# Importar WeasyPrint
# from weasyprint import HTML

from .database import engine, Base, get_db
from . import models, auth, schemas, utils

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HCE Interoperable")

# 1. Configuración de Archivos Estáticos y Plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- RUTAS DE API (Backend puro) ---

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login para clientes API (Swagger, Postman, Móvil)"""
    user = db.query(models.Usuario).filter(models.Usuario.numero_documento == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    access_token = auth.create_access_token(
        data={"sub": user.numero_documento, "role": user.rol.nombre}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- RUTAS DE FRONTEND (Vistas HTML) ---

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Muestra la pantalla de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login_web(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Procesa el formulario HTML, crea cookie y redirige"""
    user = db.query(models.Usuario).filter(models.Usuario.numero_documento == username).first()
    
    # Validación
    if not user or not utils.verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos"
        })

    # Crear Token
    access_token = auth.create_access_token(
        data={"sub": user.numero_documento, "role": user.rol.nombre}
    )
    
    # Redirigir al Dashboard (que haremos luego) guardando el token en Cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Ruta protegida:
    1. Verifica la cookie.
    2. Si no hay usuario, manda al login.
    3. Si hay usuario, mira su rol y sirve el HTML correspondiente.
    """
    user = auth.get_current_user_from_cookie(request, db)
    
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Lógica de enrutamiento por Roles
    rol = user.rol.nombre
    
    context = {"request": request, "user": user}
    
    if rol == "Medico":
        return templates.TemplateResponse("dashboard_medico.html", context)
    elif rol == "Paciente":
        # 1. Obtener datos FHIR
        observaciones_fhir = fhir_client.get_patient_observations(user.numero_documento)
        encuentros_fhir = fhir_client.get_patient_encounters(user.numero_documento)
        
        historial_agrupado = []

        # 2. Recorremos los ENCUENTROS
        for entry_enc in encuentros_fhir:
            enc_res = entry_enc.get('resource', {})
            enc_id = enc_res.get('id')
            fecha_str = enc_res.get('meta', {}).get('lastUpdated', 'N/A')[:10]
            
            # --- LÓGICA DE SEPARACIÓN DE TEXTO ---
            try:
                # Texto completo: "Gripa | Tx: Tomar agua | Obs: Reposo"
                texto_completo = enc_res.get('reasonCode', [{}])[0].get('coding', [{}])[0].get('display', 'Consulta General')
            except:
                texto_completo = "Sin Diagnóstico"

            # Valores por defecto
            diag_final = texto_completo
            tx_final = "No especificado"
            obs_final = ""

            # Separamos por el delimitador que usamos al guardar
            if " | " in texto_completo:
                partes = texto_completo.split(" | ")
                
                # La primera parte siempre es el Diagnóstico
                diag_final = partes[0]
                
                # Buscamos las otras partes
                for parte in partes[1:]:
                    if parte.startswith("Tx: "):
                        tx_final = parte.replace("Tx: ", "")
                    elif parte.startswith("Obs: "):
                        obs_final = parte.replace("Obs: ", "")
            # -------------------------------------

            # 3. Buscar Signos Vitales
            ref_buscada = f"Encounter/{enc_id}"
            signos_vitales_asociados = []
            
            for entry_obs in observaciones_fhir:
                obs_res = entry_obs.get('resource', {})
                ref_obs = obs_res.get('encounter', {}).get('reference', '')
                
                if ref_obs == ref_buscada:
                    try:
                        n_obs = obs_res.get('code', {}).get('coding', [{}])[0].get('display', 'Obs')
                    except:
                        n_obs = "Obs"
                    v = obs_res.get('valueQuantity', {}).get('value') or obs_res.get('valueString', '')
                    u = obs_res.get('valueQuantity', {}).get('unit', '')
                    signos_vitales_asociados.append(f"{n_obs}: {v} {u}")

            historial_agrupado.append({
                "fecha": fecha_str,
                "diagnostico": diag_final,   # Solo el nombre de la enfermedad
                "tratamiento": tx_final,     # Solo el tratamiento
                "observaciones": obs_final,  # Solo la observación
                "signos_vitales": signos_vitales_asociados
            })

        historial_agrupado.sort(key=lambda x: x['fecha'], reverse=True)
            
        context["historial_paciente"] = historial_agrupado
        return templates.TemplateResponse("dashboard_paciente.html", context)
    else:
        # Administrador y Admisionista
        return templates.TemplateResponse("dashboard_admin.html", context)

# --- Agrega esta nueva ruta para salir ---

@app.post("/medico/registrar", response_class=HTMLResponse)
def registrar_atencion(
    request: Request,
    paciente_doc: str = Form(...),
    diagnostico: str = Form(...),
    tratamiento: str = Form(...),
    observaciones_generales: str = Form(""), # <--- Nuevo campo (opcional)
    obs_desc: str = Form(...),
    obs_valor: str = Form(...),
    obs_unidad: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Verificar Usuario (Médico)
    medico = auth.get_current_user_from_cookie(request, db)
    if not medico or medico.rol.nombre != "Medico":
        return RedirectResponse(url="/login", status_code=303)

    # 2. Buscar Paciente
    paciente = db.query(models.Usuario).filter(models.Usuario.numero_documento == paciente_doc).first()
    context = {"request": request, "user": medico}
    
    if not paciente:
        context["msg"] = f"❌ Error: El paciente con documento {paciente_doc} no existe."
        return templates.TemplateResponse("dashboard_medico.html", context)

    # 3. Crear Encuentro en SQL
    tipo_consulta = db.query(models.TipoEncuentro).first()
    
    # --- ESTRATEGIA DE INTEROPERABILIDAD ---
    # Para FHIR: Concatenamos todo para que viaje en el recurso Encounter (reasonCode)
    # y el paciente pueda leerlo todo junto en su timeline.
    info_completa_fhir = f"{diagnostico} | Tx: {tratamiento}"
    if observaciones_generales:
        info_completa_fhir += f" | Obs: {observaciones_generales}"
    
    nuevo_encuentro = models.EncuentroMedico(
        diagnostico=info_completa_fhir, # En SQL guardamos el string completo o solo el dx segun prefieras. 
                                        # Aquí guardo el completo para consistencia con FHIR.
        observaciones_generales=observaciones_generales, # Guardamos copia limpia en columna nueva
        tipo_id=tipo_consulta.id,
        sede_id=medico.sede_id,
        medico_id=medico.id,
        paciente_id=paciente.id
    )
    db.add(nuevo_encuentro)
    db.commit()
    db.refresh(nuevo_encuentro)

    # 4. Crear Observación (Signos Vitales) en SQL
    nueva_obs = models.ObservacionClinica(
        descripcion=obs_desc,
        valor=obs_valor,
        unidad=obs_unidad,
        sede_id=medico.sede_id,
        encuentro_id=nuevo_encuentro.id
    )
    db.add(nueva_obs)
    db.commit()
    db.refresh(nueva_obs)

    # 5. --- INTEROPERABILIDAD FHIR ---
    try:
        # La función sync usará el campo .diagnostico (que ya tiene todo concatenado)
        ok_enc = fhir_client.sync_encounter_to_fhir(nuevo_encuentro)
        ok_obs = fhir_client.sync_observation_to_fhir(nueva_obs, paciente.numero_documento)
        status_fhir = "✅ Sincronizado con FHIR" if (ok_enc and ok_obs) else "⚠️ Guardado localmente, error en FHIR"
    except Exception as e:
        status_fhir = f"⚠️ Error conexión FHIR: {str(e)}"

    # 6. --- RECARGAR HISTORIAL ---
    # (Copiar aquí la misma lógica de recarga de historial que tenías antes)
    observaciones_fhir = fhir_client.get_patient_observations(paciente.numero_documento)
    encuentros_fhir = fhir_client.get_patient_encounters(paciente.numero_documento)
    
    historial_agrupado = []
    
    for entry_enc in encuentros_fhir:
        enc_res = entry_enc.get('resource', {})
        enc_id = enc_res.get('id')
        fecha_str = enc_res.get('meta', {}).get('lastUpdated', 'N/A')[:10]
        try:
            diag_txt = enc_res.get('reasonCode', [{}])[0].get('coding', [{}])[0].get('display', 'Consulta')
        except:
            diag_txt = "Sin Diagnóstico"

        ref_buscada = f"Encounter/{enc_id}"
        signos = []
        for entry_obs in observaciones_fhir:
            obs_res = entry_obs.get('resource', {})
            if obs_res.get('encounter', {}).get('reference') == ref_buscada:
                try:
                    n_obs = obs_res.get('code', {}).get('coding', [{}])[0].get('display', 'Obs')
                except:
                    n_obs = "Obs"
                v = obs_res.get('valueQuantity', {}).get('value') or obs_res.get('valueString', '')
                u = obs_res.get('valueQuantity', {}).get('unit', '')
                signos.append(f"{n_obs}: {v} {u}")

        historial_agrupado.append({
            "fecha": fecha_str,
            "diagnostico": diag_txt,
            "signos_vitales": signos
        })

    historial_agrupado.sort(key=lambda x: x['fecha'], reverse=True)

    context["msg"] = f"✅ Registro guardado para {paciente.nombres}. ({status_fhir})"
    context["paciente_actual"] = paciente
    context["historial_clinico"] = historial_agrupado
    
    return templates.TemplateResponse("dashboard_medico.html", context)

@app.get("/medico/buscar_paciente", response_class=HTMLResponse)
def medico_buscar_paciente(
    request: Request,
    q_doc: str,
    db: Session = Depends(get_db)
):
    """
    Permite al médico buscar un paciente para ver su historial cronológico
    antes de registrar una nueva atención.
    """
    medico = auth.get_current_user_from_cookie(request, db)
    if not medico or medico.rol.nombre != "Medico":
        return RedirectResponse(url="/login", status_code=303)

    # 1. Buscar Paciente en SQL
    paciente = db.query(models.Usuario).filter(models.Usuario.numero_documento == q_doc).first()
    
    context = {"request": request, "user": medico}
    
    if not paciente:
        context["msg"] = f"⚠️ Paciente con documento {q_doc} no encontrado en la base de datos."
        return templates.TemplateResponse("dashboard_medico.html", context)
    
    # 2. Si existe, traemos su HISTORIA CLÍNICA FHIR (Reusamos la lógica del paciente)
    observaciones_fhir = fhir_client.get_patient_observations(paciente.numero_documento)
    encuentros_fhir = fhir_client.get_patient_encounters(paciente.numero_documento)
    
    historial_agrupado = []

    # Procesar Encuentros
    for entry_enc in encuentros_fhir:
        enc_res = entry_enc.get('resource', {})
        enc_id = enc_res.get('id')
        fecha_str = enc_res.get('meta', {}).get('lastUpdated', 'N/A')[:10]
        
        try:
            diagnostico = enc_res.get('reasonCode', [{}])[0].get('coding', [{}])[0].get('display', 'Consulta General')
        except:
            diagnostico = "Sin Diagnóstico"

        # Buscar signos vitales de este encuentro
        referencia_buscada = f"Encounter/{enc_id}"
        signos_vitales_asociados = []
        
        for entry_obs in observaciones_fhir:
            obs_res = entry_obs.get('resource', {})
            ref_obs = obs_res.get('encounter', {}).get('reference', '')
            
            if ref_obs == referencia_buscada:
                try:
                    nombre_obs = obs_res.get('code', {}).get('coding', [{}])[0].get('display', 'Obs')
                except:
                    nombre_obs = "Observación"
                val = obs_res.get('valueQuantity', {}).get('value') or obs_res.get('valueString', 'N/A')
                unit = obs_res.get('valueQuantity', {}).get('unit', '')
                signos_vitales_asociados.append(f"{nombre_obs}: {val} {unit}")

        historial_agrupado.append({
            "fecha": fecha_str,
            "diagnostico": diagnostico,
            "signos_vitales": signos_vitales_asociados
        })

    historial_agrupado.sort(key=lambda x: x['fecha'], reverse=True)

    # Enviamos los datos al template
    context["paciente_actual"] = paciente
    context["historial_clinico"] = historial_agrupado
    
    return templates.TemplateResponse("dashboard_medico.html", context)


@app.get("/admision/buscar", response_class=HTMLResponse)
def buscar_paciente(
    request: Request,
    q_doc: str,
    db: Session = Depends(get_db)
):
    """Busca un paciente para editarlo o ver sus identificadores"""
    admin_user = auth.get_current_user_from_cookie(request, db)
    if not admin_user or admin_user.rol.nombre not in ["Administrador", "Admisionista"]:
        return RedirectResponse(url="/login", status_code=303)
    
    # Búsqueda en SQL
    paciente = db.query(models.Usuario).filter(models.Usuario.numero_documento == q_doc).first()
    
    context = {"request": request, "user": admin_user}
    
    if paciente:
        context["paciente_encontrado"] = paciente
        context["msg"] = "✅ Paciente encontrado. Puede actualizar datos o generar identificadores."
    else:
        context["msg"] = f"⚠️ No se encontró ningún paciente con el documento {q_doc}."

    return templates.TemplateResponse("dashboard_admin.html", context)

@app.post("/admision/actualizar", response_class=HTMLResponse)
def actualizar_paciente(
    request: Request,
    user_id: int = Form(...),
    nombres: str = Form(...),
    apellidos: str = Form(...),
    email: str = Form(None),
    telefono: str = Form(None),
    db: Session = Depends(get_db)
):
    """Actualiza datos básicos y resincroniza con FHIR"""
    admin_user = auth.get_current_user_from_cookie(request, db)
    if not admin_user or admin_user.rol.nombre not in ["Administrador", "Admisionista"]:
        return RedirectResponse(url="/login", status_code=303)

    # 1. Obtener el paciente de la DB
    paciente = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    
    if not paciente:
        return RedirectResponse(url="/dashboard", status_code=303)

    # 2. Actualizar datos en SQL
    paciente.nombres = nombres
    paciente.apellidos = apellidos
    paciente.email = email
    paciente.telefono = telefono
    
    db.commit()
    db.refresh(paciente)

    # 3. --- INTEROPERABILIDAD: ACTUALIZAR EN FHIR ---
    # Al llamar a sync_patient_to_fhir nuevamente con el mismo ID,
    # el servidor HAPI entiende que es un UPDATE (PUT) y actualiza los datos.
    try:
        fhir_ok = fhir_client.sync_patient_to_fhir(paciente)
        status_fhir = "✅ Actualizado en FHIR" if fhir_ok else "⚠️ Error al actualizar FHIR"
    except Exception as e:
        status_fhir = f"Error FHIR: {e}"

    context = {
        "request": request, 
        "user": admin_user,
        "paciente_encontrado": paciente,
        "msg": f"✅ Datos actualizados correctamente en SQL. ({status_fhir})"
    }
    
    return templates.TemplateResponse("dashboard_admin.html", context)

@app.get("/exportar_pdf")
def exportar_pdf(request: Request, db: Session = Depends(get_db)):
    """
    Genera la Historia Clínica en PDF usando xhtml2pdf (Compatible con Windows).
    Permite a los pacientes descargar su historia clínica completa.
    """
    user = auth.get_current_user_from_cookie(request, db)
    
    if not user or user.rol.nombre != "Paciente":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # 1. Obtener Encuentros Médicos de la BD Local
    encuentros = db.query(models.EncuentroMedico).filter(
        models.EncuentroMedico.paciente_id == user.id
    ).order_by(models.EncuentroMedico.fecha.desc()).all()
    
    encuentros_data = []
    for enc in encuentros:
        encuentros_data.append({
            "fecha": enc.fecha.strftime("%Y-%m-%d %H:%M"),
            "tipo": enc.tipo.nombre,
            "medico": f"{enc.medico.nombres} {enc.medico.apellidos}",
            "sede": enc.sede.nombre,
            "diagnostico": enc.diagnostico
        })
    
    # 2. Obtener Observaciones Clínicas de la BD Local
    observaciones_locales = []
    for enc in encuentros:
        obs_list = db.query(models.ObservacionClinica).filter(
            models.ObservacionClinica.encuentro_id == enc.id
        ).all()
        for obs in obs_list:
            observaciones_locales.append({
                "fecha": enc.fecha.strftime("%Y-%m-%d"),
                "tipo": obs.descripcion,
                "valor": obs.valor,
                "unidad": obs.unidad or ""
            })

    # 3. Obtener Datos FHIR
    try:
        observaciones_fhir = fhir_client.get_patient_observations(user.numero_documento)
        historial_fhir = []
        for entry in observaciones_fhir:
            resource = entry.get('resource', {})
            fecha_raw = resource.get('meta', {}).get('lastUpdated', 'N/A')
            fecha = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            try:
                tipo = resource.get('code', {}).get('coding', [{}])[0].get('display', 'Observación')
            except:
                tipo = "Observación"

            valor = resource.get('valueQuantity', {}).get('value') or resource.get('valueString', 'N/A')
            unidad = resource.get('valueQuantity', {}).get('unit', '')

            historial_fhir.append({
                "fecha": fecha, "tipo": tipo, "valor": valor, "unidad": unidad
            })
    except:
        historial_fhir = []

    # 4. Preparar Contexto
    context = {
        "request": request,
        "user": user,
        "encuentros": encuentros_data,
        "observaciones": observaciones_locales,
        "historial_fhir": historial_fhir,
        "today": date.today().strftime("%Y-%m-%d")
    }
    
    # 5. Renderizar HTML
    html_content = templates.TemplateResponse("pdf_template.html", context).body.decode("utf-8")
    
    # 6. Generar PDF con xhtml2pdf (pisa)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
    
    if pisa_status.err:
        return HTMLResponse("Error generando PDF", status_code=500)

    pdf_file.seek(0)
    
    # 7. Enviar al navegador para descarga
    filename = f"Historia_Clinica_{user.numero_documento}.pdf"
    
    return Response(
        content=pdf_file.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/admision/registrar_paciente", response_class=HTMLResponse)
def registrar_paciente(
    request: Request,
    nombres: str = Form(...),
    apellidos: str = Form(...),
    tipo_doc: str = Form(...),
    num_doc: str = Form(...),
    fecha_nac: str = Form(...),
    genero: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Verificar Permisos (Admin o Admisionista)
    admin_user = auth.get_current_user_from_cookie(request, db)
    # Permitimos acceso si es Administrador o Admisionista
    if not admin_user or admin_user.rol.nombre not in ["Administrador", "Admisionista"]:
        return RedirectResponse(url="/login", status_code=303)

    context = {"request": request, "user": admin_user}

    # 2. Verificar si el paciente ya existe
    existe = db.query(models.Usuario).filter(models.Usuario.numero_documento == num_doc).first()
    if existe:
        context["msg"] = f"⚠️ Error: El paciente con documento {num_doc} ya existe."
        return templates.TemplateResponse("dashboard_admin.html", context)

    try:
        # 3. Preparar datos auxiliares
        # Buscamos los IDs de los catálogos
        td_obj = db.query(models.TipoDocumento).filter(models.TipoDocumento.prefijo == tipo_doc).first()
        rol_paciente = db.query(models.Rol).filter(models.Rol.nombre == "Paciente").first()
        
        # Usamos la misma sede del admisionista para el paciente (Regla de negocio simple)
        sede_id = admin_user.sede_id

        # 4. Crear Usuario en Base de Datos (SQL)
        nuevo_paciente = models.Usuario(
            nombres=nombres,
            apellidos=apellidos,
            tipo_documento_id=td_obj.id,
            numero_documento=num_doc,
            fecha_nacimiento=datetime.strptime(fecha_nac, "%Y-%m-%d").date(),
            genero=genero,
            email=email,
            sede_id=sede_id,
            rol_id=rol_paciente.id,
            password_hash=utils.get_password_hash(password)
        )
        
        db.add(nuevo_paciente)
        db.commit()
        db.refresh(nuevo_paciente)

        # 5. --- INTEROPERABILIDAD FHIR ---
        # En cuanto se crea en SQL, se manda a HAPI FHIR
        fhir_ok = fhir_client.sync_patient_to_fhir(nuevo_paciente)
        
        msg_fhir = "✅ Sincronizado con FHIR" if fhir_ok else "⚠️ Error al sincronizar con FHIR"
        context["msg"] = f"✅ Paciente {nombres} {apellidos} creado correctamente en Citus. ({msg_fhir})"

    except Exception as e:
        db.rollback()
        context["msg"] = f"❌ Error interno: {str(e)}"

    return templates.TemplateResponse("dashboard_admin.html", context)

@app.get("/logout")
def logout():
    """Cierra sesión borrando la cookie"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response