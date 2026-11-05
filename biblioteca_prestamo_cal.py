import pandas as pd
import re
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from datetime import datetime

# =========================================================================
# PARTE 1: ARQUITECTURA ORIENTADA A OBJETOS (HERENCIA)
# =========================================================================

# CLASE BASE
class RegistroBase:
    def __init__(self, folio, fecha, nombre, grado, grupo):
        self.folio = folio
        self.fecha = fecha
        self.nombre = nombre
        self.grado = grado
        self.grupo = grupo
        
    def mostrar_registro(self):
        return f"Fecha: {self.fecha} | Folio: {self.folio} | Alumno: {self.nombre} ({self.grado}°{self.grupo})"

# CLASE DERIVADA 1 (Préstamo de Libros)
class PrestamoLibro(RegistroBase):
    def __init__(self, folio, fecha, nombre, grado, grupo, titulo_libro, estado):
        super().__init__(folio, fecha, nombre, grado, grupo)
        self.titulo_libro = titulo_libro
        self.estado = estado
        
    def mostrar_registro(self):
        datos_base = super().mostrar_registro()
        return f"[LIBRO] {datos_base} | Título: {self.titulo_libro} | Estado: {self.estado}"

# CLASE DERIVADA 2 (Uso de Espacios)
class UsoEspacio(RegistroBase):
    def __init__(self, folio, fecha, nombre, grado, grupo, area_usada):
        super().__init__(folio, fecha, nombre, grado, grupo)
        self.area_usada = area_usada
        
    def mostrar_registro(self):
        datos_base = super().mostrar_registro()
        return f"[ESPACIO] {datos_base} | Área: {self.area_usada}"

# =========================================================================
# PARTE 2: MOTOR DE PROCESAMIENTO DE DATOS (TU TRABAJO REAL)
# =========================================================================

def calcular_grado(generacion):
    if pd.isna(generacion) or str(generacion).strip() == "": 
        return "?"
    numeros = re.findall(r"\d+", str(generacion))
    for year_str in numeros:
        year = int(year_str)
        if year in [2026, 2029]: return "1"
        if year in [2025, 2028]: return "2"
        if year in [2024, 2027]: return "3"
    return "?"

def limpiar_textos_sucios(df):
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).replace(r"[\x00-\x1F\x7F]", "", regex=True)
    return df

def procesar_biblioteca():
    try:
        # 1. CARGAR DATOS
        df_padron = pd.read_csv("BD_NORMALIZADA_EJEMPLO.csv")
        df_historial = pd.read_csv("Registro_Biblioteca_EJEMPLO.csv") 

        df_padron.columns = df_padron.columns.str.upper().str.strip()
        df_historial.columns = df_historial.columns.str.upper().str.strip()

        # 2. LIMPIEZA DE ALUMNOS
        df_padron["GRADO"] = df_padron["GENERACION"].apply(calcular_grado)
        df_padron["NOMBRE_COMPLETO"] = (df_padron["APELLIDO_PATERNO"].fillna("") + " " + 
                                        df_padron["APELLIDO_MATERNO"].fillna("") + " " + 
                                        df_padron["NOMBRE"].fillna("")).str.strip()
        df_padron["NOMBRE_COMPLETO"] = df_padron["NOMBRE_COMPLETO"].str.replace(r"\s+", " ", regex=True)

        total_alumnos = len(df_padron)
        alumnos_por_grado = df_padron["GRADO"].value_counts().to_dict()
        alumnos_por_grupo = df_padron.groupby(["GRADO", "GRUPO"]).size().to_dict()

        # 3. LIMPIEZA DEL HISTORIAL
        df_historial["FECHA_SALIDA"] = pd.to_datetime(df_historial["FECHA_SALIDA"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
        df_historial["MES"] = df_historial["FECHA_SALIDA"].dt.strftime("%m-%Y").fillna("Desconocido")
        meses_disponibles = sorted([m for m in df_historial["MES"].unique() if m != "Desconocido"])

        # 4. CRUCE DE DATOS
        df_completo = pd.merge(df_historial, df_padron, left_on="FOLIO_ALUMNO", right_on="FOLIO", how="left")
        total_prestamos = len(df_completo[df_completo["FECHA_SALIDA"].notna()])

        # --- REQUERIMIENTOS: CÁLCULOS ESTADÍSTICOS ---
        
        # Índice Global
        fila_global = {
            "MÉTRICA": "Global Escuela",
            "ALUMNOS_MATRICULADOS": total_alumnos,
            "PRÉSTAMOS_ANUAL": total_prestamos,
            "ÍNDICE_ANUAL": round(total_prestamos / total_alumnos, 4) if total_alumnos > 0 else 0
        }
        for m in meses_disponibles:
            prest_mes = len(df_completo[df_completo["MES"] == m])
            fila_global[f"PRÉSTAMOS_{m}"] = prest_mes
            fila_global[f"ÍNDICE_{m}"] = round(prest_mes / total_alumnos, 4) if total_alumnos > 0 else 0
        df_global_final = pd.DataFrame([fila_global])

        # Índice por Grado
        filas_grados = []
        for g in ["1", "2", "3"]:
            alumnos = alumnos_por_grado.get(g, 0)
            prest_anual = len(df_completo[(df_completo["GRADO"] == g) & (df_completo["FECHA_SALIDA"].notna())])
            fila = {"GRADO": g, "ALUMNOS_MATRICULADOS": alumnos, "PRÉSTAMOS_ANUAL": prest_anual, "ÍNDICE_ANUAL": round(prest_anual / alumnos, 4) if alumnos > 0 else 0}
            for m in meses_disponibles:
                prest_mes = len(df_completo[(df_completo["GRADO"] == g) & (df_completo["MES"] == m)])
                fila[f"PRÉSTAMOS_{m}"] = prest_mes
                fila[f"ÍNDICE_{m}"] = round(prest_mes / alumnos, 4) if alumnos > 0 else 0
            filas_grados.append(fila)
        df_grado_final = pd.DataFrame(filas_grados)

        # Índice por Grupo
        filas_grupos = []
        for g_num in ["1", "2", "3"]:
            for g_letra in ["A", "B", "C", "D", "E", "F"]:
                alumnos = alumnos_por_grupo.get((g_num, g_letra), 0)
                prest_anual = len(df_completo[(df_completo["GRADO"] == g_num) & (df_completo["GRUPO"] == g_letra) & (df_completo["FECHA_SALIDA"].notna())])
                fila = {"GRADO": g_num, "GRUPO": g_letra, "ALUMNOS_MATRICULADOS": alumnos, "PRÉSTAMOS_ANUAL": prest_anual, "ÍNDICE_ANUAL": round(prest_anual / alumnos, 4) if alumnos > 0 else 0}
                for m in meses_disponibles:
                    prest_mes = len(df_completo[(df_completo["GRADO"] == g_num) & (df_completo["GRUPO"] == g_letra) & (df_completo["MES"] == m)])
                    fila[f"PRÉSTAMOS_{m}"] = prest_mes
                    fila[f"ÍNDICE_{m}"] = round(prest_mes / alumnos, 4) if alumnos > 0 else 0
                filas_grupos.append(fila)
        df_grupo_final = pd.DataFrame(filas_grupos)

        # Top Lectores, Resumen y Deudores
        top_alumnos_df = df_completo.groupby(["FOLIO", "NOMBRE_COMPLETO", "GRADO", "GRUPO"]).size().reset_index(name="TOTAL_LIBROS")
        top_alumnos_df = top_alumnos_df.sort_values(by="TOTAL_LIBROS", ascending=False)
        mejor_alumno_texto = f"{top_alumnos_df.iloc[0]['NOMBRE_COMPLETO']} ({top_alumnos_df.iloc[0]['GRADO']}{top_alumnos_df.iloc[0]['GRUPO']})" if not top_alumnos_df.empty else "N/A"

        en_circulacion = df_historial[df_historial["ESTADO"].str.contains("PRESTADO", na=False, case=False)].shape[0]
        devueltos = df_historial[df_historial["ESTADO"].str.contains("DEVUELTO", na=False, case=False)].shape[0]

        df_resumen = pd.DataFrame({
            "MÉTRICA": ["Libros en Circulación (Prestados)", "Libros Devueltos", "Alumno Top Lector #1"],
            "VALOR": [en_circulacion, devueltos, mejor_alumno_texto]
        })

        df_deudores = df_completo[df_completo["ESTADO"].str.contains("PRESTADO", na=False, case=False)]
        df_deudores = df_deudores[["NOMBRE_COMPLETO", "GRADO", "GRUPO", "FOLIO", "FECHA_SALIDA"]].sort_values(by=["GRADO", "GRUPO", "NOMBRE_COMPLETO"])
        df_deudores["FECHA_SALIDA"] = df_deudores["FECHA_SALIDA"].dt.strftime("%d/%m/%Y")

        # =========================================================================
        # PARTE 3: DEMOSTRACIÓN DE HERENCIA EN CONSOLA (Para validación de la tarea)
        # =========================================================================
        print("\n=== SISTEMA DE BIBLIOTECA: DEMOSTRACIÓN DE HERENCIA ===")
        print("Convirtiendo los últimos registros de Pandas en Objetos Python...\n")
        
        # Tomamos datos reales de tu DataFrame y los convertimos en objetos PrestamoLibro
        for index, row in df_completo.head(2).iterrows():
            fecha_str = row["FECHA_SALIDA"].strftime("%d/%m/%Y") if pd.notnull(row["FECHA_SALIDA"]) else "Desconocida"
            obj_libro = PrestamoLibro(
                folio=row["FOLIO"], 
                fecha=fecha_str,
                nombre=row["NOMBRE_COMPLETO"], 
                grado=row["GRADO"], 
                grupo=row["GRUPO"],
                titulo_libro=row.get("LIBRO", "Sin Título"),
                estado=row.get("ESTADO", "Desconocido")
            )
            print(obj_libro.mostrar_registro())
            
        # Simulamos registros de UsoEspacio para demostrar polimorfismo
        obj_espacio = UsoEspacio("8055", datetime.today().strftime("%d/%m/%Y"), "Edmundo González", "3", "A", "Mesa 4")
        print(obj_espacio.mostrar_registro())
        print("=======================================================\n")

        # =========================================================================
        # PARTE 4: EXPORTACIÓN A EXCEL
        # =========================================================================
        archivo_salida = "Analitica_Biblioteca_Format.xlsx"
        hojas = {
            "Índice_Global": limpiar_textos_sucios(df_global_final),
            "Índice_Por_Grado": limpiar_textos_sucios(df_grado_final),
            "Índice_Por_Grupo": limpiar_textos_sucios(df_grupo_final),
            "Resumen_General": limpiar_textos_sucios(df_resumen),
            "Top_10_Lectores": limpiar_textos_sucios(top_alumnos_df[["NOMBRE_COMPLETO", "GRADO", "GRUPO", "TOTAL_LIBROS"]].head(10)),
            "Lista_Deudores": limpiar_textos_sucios(df_deudores)
        }

        with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
            for nombre_hoja, dataframe in hojas.items():
                dataframe.to_excel(writer, sheet_name=nombre_hoja, index=False)
                worksheet = writer.sheets[nombre_hoja]
                
                fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
                font = Font(color="FFFFFF", bold=True)
                align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                thin_border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
                
                for col_idx, col_name in enumerate(dataframe.columns, 1):
                    cell = worksheet.cell(row=1, column=col_idx)
                    cell.fill = fill
                    cell.font = font
                    cell.alignment = align
                    cell.border = thin_border
                    max_len = max(dataframe[col_name].astype(str).map(len).max() if not dataframe.empty else 0, len(str(col_name))) + 2
                    worksheet.column_dimensions[cell.column_letter].width = min(max_len, 40)
                    for row_idx in range(2, len(dataframe) + 2):
                        worksheet.cell(row=row_idx, column=col_idx).border = thin_border

        print(f"Éxito: Se generó el archivo {archivo_salida} con 6 pestañas.")

    except Exception as e:
        print(f"Error en el procesamiento: {e}")

if __name__ == "__main__":
    procesar_biblioteca()