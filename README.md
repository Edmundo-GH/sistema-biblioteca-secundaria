# Sistema de Gestión y Analítica para Biblioteca Escolar 📚

Proyecto desarrollado para una escuela secundaria pública, enfocado en automatizar el control de préstamos de libros, seguimiento de deudores y cálculo del índice lector mediante una arquitectura híbrida.

## 🚀 Arquitectura del Sistema

El sistema combina tecnologías Cloud y procesamiento local por lotes:

1. **Frontend (AppSheet + Google Sheets):** Aplicación móvil implementada para la captura ágil de folios y metadatos de préstamos desde campo.
2. **Backend / Motor Analítico (Java):** Motor de procesamiento robusto desarrollado con Programación Orientada a Objetos (POO), manejo de estructuras de datos (`HashMap`, `ArrayList`) y limpieza de cadenas mediante Expresiones Regulares (Regex).
3. **Métrica de Impacto (Índice Lector):** Cálculo automatizado del promedio de libros leídos por alumno a nivel general y desglosado por mes y grupo.

## 📂 Estructura del Repositorio

- `Main.java` - Código fuente del motor analítico.
- `BD_NORMALIZADA_EJEMPLO.csv` - Estructura de prueba anónima para validación del sistema.
- `README.md` - Documentación técnica del proyecto.

## ⚙ Tecnologías Utilizadas

- **Java (JDK 17+)**
- **AppSheet / Google Workspace**
- **Git & GitHub**
