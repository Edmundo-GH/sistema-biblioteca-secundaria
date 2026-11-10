"""
modelos.py
----------
Define la estructura de clases del sistema (requisito académico POO + Herencia).

Jerarquía:
    Alumno            -> Entidad del padrón
    PrestamoLibro     -> Entidad de préstamo individual (usada en el CSV de AppSheet)
    RegistroBiblioteca (ABSTRACTA)  -> Clase padre de cualquier registro de servicio
        ├── Prestamo            -> Salida/devolución de libro
        └── ServicioEstancia    -> Estancia, lectura, ajedrez, evento grupal, etc.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import re


# =========================================================
# FUNCIÓN DE APOYO: cálculo de grado a partir de GENERACION
# =========================================================
def calcular_grado(generacion) -> str:
    """
    Calcula el grado (1, 2 o 3) a partir del campo GENERACION.
    Se aceptan formatos como '2026', '2024-2027', 'Generación 2025', etc.
    """
    if generacion is None:
        return "?"
    texto = str(generacion).strip()
    if texto == "" or texto.lower() == "nan":
        return "?"

    years = re.findall(r"\d{4}", texto)
    for y in years:
        y = int(y)
        if y in (2026, 2029):
            return "1"
        if y in (2025, 2028):
            return "2"
        if y in (2024, 2027):
            return "3"
    return "?"


# =========================================================
# CLASE: Alumno
# =========================================================
@dataclass
class Alumno:
    """Representa a un alumno del padrón."""
    folio: str
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    grupo: str
    generacion: str
    correo: str = ""

    @property
    def grado(self) -> str:
        return calcular_grado(self.generacion)

    @property
    def nombre_completo(self) -> str:
        return " ".join(
            p for p in (self.apellido_paterno, self.apellido_materno, self.nombre) if p
        ).strip()

    def __str__(self):
        return f"{self.nombre_completo} ({self.grado}°{self.grupo})"


# =========================================================
# CLASE: PrestamoLibro (entidad individual, usada en importación)
# =========================================================
@dataclass
class PrestamoLibro:
    """
    Representa un préstamo tal cual viene del CSV de AppSheet.
    Es una entidad de datos, NO la usamos para la jerarquía de RegistroBiblioteca.
    """
    id_prestamo: str
    folio_alumno: str
    fecha_salida: datetime
    estado: str                      # "Prestado" o "Devuelto"
    fecha_devolucion: datetime | None = None
    datos_libro: str = ""


# =========================================================
# CLASE ABSTRACTA: RegistroBiblioteca (PADRE)
# =========================================================
class RegistroBiblioteca(ABC):
    """
    Clase base de cualquier evento registrado en la biblioteca.
    Cumple el requisito de herencia: Prestamo y ServicioEstancia heredan de aquí.
    """

    def __init__(self, fecha_hora: datetime | None = None, origen: str = "Manual"):
        self.fecha_hora: datetime = fecha_hora or datetime.now()
        self.origen: str = origen  # "Manual", "AppSheet", "Estancia", "Evento"

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Devuelve una etiqueta legible del tipo de registro."""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Serializa el registro a un diccionario para exportar a CSV/Excel."""
        ...

    def __repr__(self):
        return f"<{self.__class__.__name__} | {self.fecha_hora:%d/%m/%Y %H:%M}>"


# =========================================================
# HIJA 1: Prestamo  (salida/devolución de libro)
# =========================================================
class Prestamo(RegistroBiblioteca):
    """
    Representa la salida (y eventual devolución) de un libro a un alumno.
    Hereda de RegistroBiblioteca.
    """

    def __init__(self, folio_alumno: str, estado: str = "Prestado",
                 fecha_devolucion: datetime | None = None,
                 datos_libro: str = "",
                 id_prestamo: str | None = None,
                 fecha_hora: datetime | None = None,
                 origen: str = "Manual"):
        super().__init__(fecha_hora=fecha_hora, origen=origen)
        self.id_prestamo = id_prestamo or self._generar_id()
        self.folio_alumno = folio_alumno
        self.estado = estado
        self.fecha_devolucion = fecha_devolucion
        self.datos_libro = datos_libro

    @staticmethod
    def _generar_id() -> str:
        import uuid
        return uuid.uuid4().hex[:8]

    @property
    def tipo(self) -> str:
        return "Préstamo de libro"

    @property
    def esta_devuelto(self) -> bool:
        return self.estado.strip().lower() == "devuelto"

    def to_dict(self) -> dict:
        return {
            "ID_Prestamo": self.id_prestamo,
            "Folio_Alumno": self.folio_alumno,
            "Fecha_Salida": self.fecha_hora.strftime("%d/%m/%Y %H:%M:%S"),
            "Datos_Extraidos": self.datos_libro,
            "Estado": self.estado,
            "Fecha_Devolucion": (
                self.fecha_devolucion.strftime("%d/%m/%Y %H:%M:%S")
                if self.fecha_devolucion else ""
            ),
            "Origen": self.origen,
        }


# =========================================================
# HIJA 2: ServicioEstancia  (estancia, lectura, evento, ajedrez…)
# =========================================================
class ServicioEstancia(RegistroBiblioteca):
    """
    Representa un servicio en la biblioteca sin préstamo de libro:
    estancia, lectura, ajedrez, trabajo al margen, junta grupal, charla, etc.
    Hereda de RegistroBiblioteca.
    """

    TIPOS_VALIDOS = (
        "Trabajo al margen del grupo",
        "Lectura en sala",
        "Ajedrez",
        "Maestro responsable",
        "Evento grupal",
        "Otro",
    )

    def __init__(self, tipo_servicio: str, folio_alumno: str = "",
                 nombre_alumno: str = "", grado: str = "", grupo: str = "",
                 responsable: str = "", cantidad_personas: int = 1,
                 fecha_hora: datetime | None = None, origen: str = "Estancia"):
        super().__init__(fecha_hora=fecha_hora, origen=origen)
        if tipo_servicio not in self.TIPOS_VALIDOS:
            tipo_servicio = "Otro"
        self.tipo_servicio = tipo_servicio
        self.folio_alumno = folio_alumno
        self.nombre_alumno = nombre_alumno
        self.grado = grado
        self.grupo = grupo
        self.responsable = responsable
        self.cantidad_personas = max(1, int(cantidad_personas))

    @property
    def tipo(self) -> str:
        return self.tipo_servicio

    @property
    def es_evento_grupal(self) -> bool:
        return self.tipo_servicio == "Evento grupal"

    def to_dict(self) -> dict:
        return {
            "Fecha_Hora": self.fecha_hora.strftime("%d/%m/%Y %H:%M:%S"),
            "Tipo_Servicio": self.tipo_servicio,
            "Folio_Alumno": self.folio_alumno,
            "Nombre_Alumno": self.nombre_alumno,
            "Grado": self.grado,
            "Grupo": self.grupo,
            "Responsable": self.responsable,
            "Cantidad_Personas": self.cantidad_personas,
            "Origen": self.origen,
        }