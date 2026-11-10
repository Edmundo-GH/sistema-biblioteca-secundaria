"""
motor_datos.py
--------------
Capa de datos: carga de CSV, conversión a objetos POO, generación de KPIs
(incluye servicios/estancias) y exportación a Excel.
"""

from __future__ import annotations
import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional

from modelos import (
    Alumno, PrestamoLibro, Prestamo, ServicioEstancia,
    RegistroBiblioteca, calcular_grado,
)
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


# =========================================================
# Repositorio central
# =========================================================
class BibliotecaRepositorio:
    def __init__(self):
        self.alumnos: dict[str, Alumno] = {}
        self.registros: list[RegistroBiblioteca] = []
        self.ruta_padron: Optional[Path] = None
        self.ruta_historial: Optional[Path] = None

    # ---------------------- CARGA ----------------------
    def cargar_padron(self, ruta: str | Path) -> int:
        ruta = Path(ruta)
        df = pd.read_csv(ruta, dtype=str)
        df.columns = df.columns.str.strip().str.upper()

        requeridas = {"FOLIO", "NOMBRE", "APELLIDO_PATERNO", "APELLIDO_MATERNO", "GRUPO", "GENERACION"}
        faltantes = requeridas - set(df.columns)
        if faltantes:
            raise ValueError(f"Faltan columnas en el padrón: {faltantes}")

        self.alumnos.clear()
        for _, row in df.iterrows():
            folio = str(row["FOLIO"]).strip()
            if not folio or folio.lower() == "nan":
                continue
            self.alumnos[folio] = Alumno(
                folio=folio,
                nombre=str(row.get("NOMBRE", "")).strip(),
                apellido_paterno=str(row.get("APELLIDO_PATERNO", "")).strip(),
                apellido_materno=str(row.get("APELLIDO_MATERNO", "")).strip(),
                grupo=str(row.get("GRUPO", "")).strip().upper(),
                generacion=str(row.get("GENERACION", "")).strip(),
                correo=str(row.get("CORREO", "")).strip(),
            )
        self.ruta_padron = ruta
        return len(self.alumnos)

    def cargar_historial(self, ruta: str | Path, origen: str = "AppSheet") -> int:
        ruta = Path(ruta)
        df = pd.read_csv(ruta, dtype=str)
        df.columns = df.columns.str.strip().str.upper()
        cargados = 0
        for _, row in df.iterrows():
            try:
                folio = str(row.get("FOLIO_ALUMNO", "")).strip()
                if not folio or folio.lower() == "nan":
                    continue
                fecha_salida = pd.to_datetime(
                    row.get("FECHA_SALIDA", ""), format="%d/%m/%Y %H:%M:%S", errors="coerce"
                )
                fecha_dev = pd.to_datetime(
                    row.get("FECHA_DEVOLUCION", ""), format="%d/%m/%Y %H:%M:%S", errors="coerce"
                )
                self.registros.append(Prestamo(
                    folio_alumno=folio,
                    estado=str(row.get("ESTADO", "Prestado")).strip() or "Prestado",
                    fecha_devolucion=None if pd.isna(fecha_dev) else fecha_dev.to_pydatetime(),
                    datos_libro=str(row.get("DATOS_EXTRAIDOS", "") or ""),
                    id_prestamo=str(row.get("ID_PRESTAMO", "") or None),
                    fecha_hora=None if pd.isna(fecha_salida) else fecha_salida.to_pydatetime(),
                    origen=origen,
                ))
                cargados += 1
            except Exception as e:
                print(f"[!] Fila de historial ignorada: {e}")
        self.ruta_historial = ruta
        return cargados

    def agregar_prestamo(self, folio: str, estado: str = "Prestado") -> Prestamo:
        p = Prestamo(folio_alumno=folio, estado=estado, origen="Manual")
        self.registros.append(p)
        return p

    def agregar_servicio(self, **kwargs) -> ServicioEstancia:
        s = ServicioEstancia(**kwargs)
        self.registros.append(s)
        return s

    # ---------------------- CONSULTAS ----------------------
    def buscar_alumno(self, folio: str) -> Optional[Alumno]:
        return self.alumnos.get(str(folio).strip())

    def buscar_alumnos_fuzzy(self, texto: str, grado: str = "", grupo: str = "") -> list[Alumno]:
        texto = (texto or "").strip().lower()
        resultados = []
        for a in self.alumnos.values():
            if grado and a.grado != grado:
                continue
            if grupo and a.grupo != grupo:
                continue
            if not texto or texto in a.nombre_completo.lower() or texto in a.folio:
                resultados.append(a)
        return sorted(resultados, key=lambda x: x.nombre_completo)

    def guardar_registros_csv(self, ruta: str | Path) -> None:
        filas = [r.to_dict() for r in self.registros if isinstance(r, Prestamo)]
        if not filas:
            return
        df = pd.DataFrame(filas)
        df.to_csv(ruta, index=False, encoding="utf-8-sig")


# =========================================================
# ANALÍTICA — PRÉSTAMOS
# =========================================================
def limpiar_textos_sucios(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).replace(r"[\x00-\x1F\x7F]", "", regex=True)
    return df


def construir_dataframes(repo: BibliotecaRepositorio) -> tuple[pd.DataFrame, pd.DataFrame]:
    filas_padron = []
    for a in repo.alumnos.values():
        filas_padron.append({
            "FOLIO": a.folio, "NOMBRE": a.nombre,
            "APELLIDO_PATERNO": a.apellido_paterno,
            "APELLIDO_MATERNO": a.apellido_materno,
            "GRUPO": a.grupo, "GENERACION": a.generacion,
            "CORREO": a.correo, "GRADO": a.grado,
            "NOMBRE_COMPLETO": a.nombre_completo,
        })
    df_padron = pd.DataFrame(filas_padron)

    filas_hist = []
    for r in repo.registros:
        if isinstance(r, Prestamo):
            filas_hist.append(r.to_dict())
    df_hist = pd.DataFrame(filas_hist)
    if not df_hist.empty:
        df_hist.columns = df_hist.columns.str.upper()
        df_hist["FECHA_SALIDA"] = pd.to_datetime(
            df_hist["FECHA_SALIDA"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
        )
        df_hist["FECHA_DEVOLUCION"] = pd.to_datetime(
            df_hist["FECHA_DEVOLUCION"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
        )
        df_hist["MES"] = df_hist["FECHA_SALIDA"].dt.strftime("%m-%Y").fillna("Desconocido")
    return df_padron, df_hist


def calcular_kpis(repo: BibliotecaRepositorio) -> dict:
    df_padron, df_hist = construir_dataframes(repo)
    total_alumnos = len(df_padron)
    alumnos_por_grado = df_padron["GRADO"].value_counts().to_dict() if not df_padron.empty else {}
    alumnos_por_grupo = (
        df_padron.groupby(["GRADO", "GRUPO"]).size().to_dict() if not df_padron.empty else {}
    )

    if not df_hist.empty:
        df_hist = df_hist.rename(columns={"FOLIO_ALUMNO": "FOLIO"})
        df_completo = pd.merge(df_hist, df_padron, on="FOLIO", how="left")
        total_prestamos = len(df_completo[df_completo["FECHA_SALIDA"].notna()])
        meses = sorted([m for m in df_completo["MES"].unique() if m != "Desconocido"])
    else:
        df_completo = df_padron.iloc[0:0]
        total_prestamos = 0
        meses = []

    fila_global = {
        "METRICA": "Global Escuela",
        "ALUMNOS_MATRICULADOS": total_alumnos,
        "PRESTAMOS_ANUAL": total_prestamos,
        "INDICE_ANUAL": round(total_prestamos / total_alumnos, 4) if total_alumnos else 0,
    }
    for m in meses:
        pm = len(df_completo[df_completo["MES"] == m]) if not df_completo.empty else 0
        fila_global[f"PRESTAMOS_{m}"] = pm
        fila_global[f"INDICE_{m}"] = round(pm / total_alumnos, 4) if total_alumnos else 0
    df_global = pd.DataFrame([fila_global])

    filas_g = []
    for g in ["1", "2", "3"]:
        alumnos = alumnos_por_grado.get(g, 0)
        if not df_completo.empty and "GRADO" in df_completo.columns:
            p_anual = len(df_completo[(df_completo["GRADO"] == g) & df_completo["FECHA_SALIDA"].notna()])
        else:
            p_anual = 0
        fila = {"GRADO": g, "ALUMNOS_MATRICULADOS": alumnos, "PRESTAMOS_ANUAL": p_anual,
                "INDICE_ANUAL": round(p_anual / alumnos, 4) if alumnos else 0}
        for m in meses:
            if not df_completo.empty:
                pm = len(df_completo[(df_completo["GRADO"] == g) & (df_completo["MES"] == m)])
            else:
                pm = 0
            fila[f"PRESTAMOS_{m}"] = pm
            fila[f"INDICE_{m}"] = round(pm / alumnos, 4) if alumnos else 0
        filas_g.append(fila)
    df_grado = pd.DataFrame(filas_g)

    filas_gp = []
    for gn in ["1", "2", "3"]:
        for gl in ["A", "B", "C", "D", "E", "F"]:
            alumnos = alumnos_por_grupo.get((gn, gl), 0)
            if alumnos == 0:
                continue
            if not df_completo.empty:
                p_anual = len(df_completo[
                    (df_completo["GRADO"] == gn) &
                    (df_completo["GRUPO"] == gl) &
                    df_completo["FECHA_SALIDA"].notna()
                ])
            else:
                p_anual = 0
            fila = {"GRADO": gn, "GRUPO": gl, "ALUMNOS_MATRICULADOS": alumnos,
                    "PRESTAMOS_ANUAL": p_anual,
                    "INDICE_ANUAL": round(p_anual / alumnos, 4) if alumnos else 0}
            for m in meses:
                if not df_completo.empty:
                    pm = len(df_completo[
                        (df_completo["GRADO"] == gn) &
                        (df_completo["GRUPO"] == gl) &
                        (df_completo["MES"] == m)
                    ])
                else:
                    pm = 0
                fila[f"PRESTAMOS_{m}"] = pm
                fila[f"INDICE_{m}"] = round(pm / alumnos, 4) if alumnos else 0
            filas_gp.append(fila)
    df_grupo = pd.DataFrame(filas_gp)

    if not df_completo.empty and "NOMBRE_COMPLETO" in df_completo.columns:
        top = (
            df_completo.dropna(subset=["NOMBRE_COMPLETO"])
            .groupby(["NOMBRE_COMPLETO", "GRADO", "GRUPO"], dropna=False)
            .size().reset_index(name="TOTAL_LIBROS")
            .sort_values("TOTAL_LIBROS", ascending=False)
            .head(15)
        )
    else:
        top = pd.DataFrame(columns=["NOMBRE_COMPLETO", "GRADO", "GRUPO", "TOTAL_LIBROS"])

    COLUMNAS_DEUDORES = ["NOMBRE_COMPLETO", "GRADO", "GRUPO", "FOLIO", "CORREO", "FECHA_SALIDA"]
    if not df_completo.empty and "ESTADO" in df_completo.columns:
        mask = df_completo["ESTADO"].astype(str).str.upper().str.contains("PRESTADO", na=False)
        deudores = df_completo[mask].copy()
        for col in COLUMNAS_DEUDORES:
            if col not in deudores.columns:
                deudores[col] = ""
        deudores = deudores[COLUMNAS_DEUDORES].copy()
        if not deudores.empty:
            deudores["FECHA_SALIDA"] = pd.to_datetime(
                deudores["FECHA_SALIDA"], errors="coerce"
            ).dt.strftime("%d/%m/%Y")
            deudores["GRADO"] = deudores["GRADO"].astype(str)
            deudores["GRUPO"] = deudores["GRUPO"].astype(str)
            deudores["NOMBRE_COMPLETO"] = deudores["NOMBRE_COMPLETO"].astype(str)
            deudores = deudores.sort_values(
                by=["GRADO", "GRUPO", "NOMBRE_COMPLETO"],
                ascending=[True, True, True], na_position="last",
            ).reset_index(drop=True)
    else:
        deudores = pd.DataFrame(columns=COLUMNAS_DEUDORES)

    en_circulacion = (
        int(df_hist["ESTADO"].astype(str).str.upper().str.contains("PRESTADO", na=False).sum())
        if not df_hist.empty else 0
    )
    devueltos = (
        int(df_hist["ESTADO"].astype(str).str.upper().str.contains("DEVUELTO", na=False).sum())
        if not df_hist.empty else 0
    )
    mejor = "N/A"
    if not top.empty:
        fila = top.iloc[0]
        mejor = f"{fila['NOMBRE_COMPLETO']} ({fila['GRADO']}°{fila['GRUPO']}) - {fila['TOTAL_LIBROS']} libros"

    df_resumen = pd.DataFrame({
        "METRICA": [
            "Libros en circulación (Prestado)", "Libros devueltos",
            "Alumno Top Lector #1", "Total de registros analizados",
        ],
        "VALOR": [
            en_circulacion, devueltos, mejor,
            len(df_completo) if not df_completo.empty else 0,
        ],
    })

    return {
        "global": df_global, "por_grado": df_grado, "por_grupo": df_grupo,
        "top_lectores": top, "deudores": deudores, "resumen": df_resumen,
        "df_completo": df_completo,
    }


# =========================================================
# ANALÍTICA — SERVICIOS / ESTANCIAS
# =========================================================
def construir_df_servicios(repo: BibliotecaRepositorio) -> pd.DataFrame:
    """Devuelve un DataFrame con todos los servicios/estancias registrados."""
    filas = []
    for r in repo.registros:
        if isinstance(r, ServicioEstancia):
            filas.append(r.to_dict())
    if not filas:
        return pd.DataFrame(columns=[
            "Fecha_Hora", "Tipo_Servicio", "Folio_Alumno", "Nombre_Alumno",
            "Grado", "Grupo", "Responsable", "Cantidad_Personas", "Origen"
        ])
    df = pd.DataFrame(filas)
    try:
        df["_dt"] = pd.to_datetime(df["Fecha_Hora"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
        df = df.sort_values("_dt", ascending=False).drop(columns=["_dt"])
    except Exception:
        pass
    return df


def calcular_kpis_servicios(repo: BibliotecaRepositorio) -> dict:
    df = construir_df_servicios(repo)

    if df.empty:
        return {
            "total": 0, "eventos": 0, "personas_eventos": 0,
            "por_tipo": pd.DataFrame(columns=["TIPO_SERVICIO", "CANTIDAD"]),
            "por_grado": pd.DataFrame(columns=["GRADO", "CANTIDAD"]),
            "top_alumnos": pd.DataFrame(columns=["NOMBRE_ALUMNO", "GRADO", "GRUPO", "VISITAS"]),
            "df": df,
        }

    total = len(df)
    eventos_mask = df["Tipo_Servicio"] == "Evento grupal"
    eventos = int(eventos_mask.sum())
    personas_eventos = int(
        pd.to_numeric(df.loc[eventos_mask, "Cantidad_Personas"], errors="coerce").fillna(0).sum()
    )

    por_tipo = (
        df.groupby("Tipo_Servicio").size().reset_index(name="CANTIDAD")
        .rename(columns={"Tipo_Servicio": "TIPO_SERVICIO"})
        .sort_values("CANTIDAD", ascending=False)
    )

    df_ind = df[~eventos_mask].copy()
    df_ind["Grado"] = df_ind["Grado"].astype(str)
    por_grado = (
        df_ind[df_ind["Grado"].isin(["1", "2", "3"])]
        .groupby("Grado").size().reset_index(name="CANTIDAD")
        .rename(columns={"Grado": "GRADO"}).sort_values("GRADO")
    )

    top_alumnos = (
        df_ind[df_ind["Nombre_Alumno"].notna() & (df_ind["Nombre_Alumno"] != "")]
        .groupby(["Nombre_Alumno", "Grado", "Grupo"], dropna=False)
        .size().reset_index(name="VISITAS")
        .rename(columns={"Nombre_Alumno": "NOMBRE_ALUMNO",
                         "Grado": "GRADO", "Grupo": "GRUPO"})
        .sort_values("VISITAS", ascending=False).head(10)
    )

    return {
        "total": total, "eventos": eventos, "personas_eventos": personas_eventos,
        "por_tipo": por_tipo, "por_grado": por_grado,
        "top_alumnos": top_alumnos, "df": df,
    }


# =========================================================
# EXPORTACIÓN EXCEL (todo junto: préstamos + servicios)
# =========================================================
def exportar_excel(kpis: dict, ruta_salida: str | Path,
                   repo: BibliotecaRepositorio | None = None) -> str:
    ruta_salida = Path(ruta_salida)
    hojas = {
        "Indice_Global": kpis["global"],
        "Indice_Por_Grado": kpis["por_grado"],
        "Indice_Por_Grupo": kpis["por_grupo"],
        "Resumen_General": kpis["resumen"],
        "Top_10_Lectores": kpis["top_lectores"].head(10),
        "Lista_Deudores": kpis["deudores"],
    }

    if repo is not None:
        ks = calcular_kpis_servicios(repo)
        hojas["Servicios_Listado"] = ks["df"]
        hojas["Servicios_Por_Tipo"] = ks["por_tipo"]
        hojas["Servicios_Por_Grado"] = ks["por_grado"]
        hojas["Servicios_Top_Alumnos"] = ks["top_alumnos"]

    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        for nombre, df in hojas.items():
            df_limpio = limpiar_textos_sucios(df.copy())
            df_limpio.to_excel(writer, sheet_name=nombre, index=False)
            try:
                ws = writer.sheets[nombre]
                fill = PatternFill("solid", start_color="1F497D")
                font = Font(color="FFFFFF", bold=True)
                align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                thin = Border(
                    left=Side(style="thin"), right=Side(style="thin"),
                    top=Side(style="thin"), bottom=Side(style="thin"),
                )
                for c_idx, col in enumerate(df_limpio.columns, 1):
                    cell = ws.cell(row=1, column=c_idx)
                    cell.fill = fill
                    cell.font = font
                    cell.alignment = align
                    cell.border = thin
                    try:
                        serie_str = df_limpio[col].astype(str).fillna("")
                        longitudes = serie_str.map(lambda x: len(str(x)) if x is not None else 0)
                        max_dato = int(longitudes.max()) if len(longitudes) > 0 else 0
                    except Exception:
                        max_dato = 0
                    max_len = max(max_dato, len(str(col))) + 2
                    ws.column_dimensions[cell.column_letter].width = min(max_len, 40)
                    for r_idx in range(2, len(df_limpio) + 2):
                        ws.cell(row=r_idx, column=c_idx).border = thin
            except Exception as e:
                print(f"[aviso] Formato visual de '{nombre}' falló: {e}")

    if not ruta_salida.exists():
        raise RuntimeError(f"El archivo no se creó: {ruta_salida}")
    if ruta_salida.stat().st_size == 0:
        raise RuntimeError(f"El archivo quedó vacío: {ruta_salida}")
    return str(ruta_salida)