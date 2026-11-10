"""
persistencia.py
---------------
Guarda y carga el estado completo del repositorio en un JSON local,
para que la app tenga "memoria" entre sesiones.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

from modelos import Alumno, Prestamo, ServicioEstancia
from motor_datos import BibliotecaRepositorio

ARCHIVO_DATOS = Path(__file__).parent / "biblioteca_data.json"


def guardar_repositorio(repo: BibliotecaRepositorio, ruta: Path = ARCHIVO_DATOS) -> None:
    """Serializa alumnos + registros a JSON."""
    data = {
        "version": 1,
        "guardado_en": datetime.now().isoformat(),
        "alumnos": [
            {
                "folio": a.folio,
                "nombre": a.nombre,
                "apellido_paterno": a.apellido_paterno,
                "apellido_materno": a.apellido_materno,
                "grupo": a.grupo,
                "generacion": a.generacion,
                "correo": a.correo,
            }
            for a in repo.alumnos.values()
        ],
        "registros": [],
    }
    for r in repo.registros:
        if isinstance(r, Prestamo):
            data["registros"].append({"tipo": "prestamo", **r.to_dict(),
                                       "fecha_iso": r.fecha_hora.isoformat()})
        elif isinstance(r, ServicioEstancia):
            data["registros"].append({"tipo": "servicio", **r.to_dict(),
                                       "fecha_iso": r.fecha_hora.isoformat()})

    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_repositorio(repo: BibliotecaRepositorio, ruta: Path = ARCHIVO_DATOS) -> bool:
    """Carga el JSON. Devuelve True si encontró datos previos."""
    if not ruta.exists():
        return False
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return False

    repo.alumnos.clear()
    repo.registros.clear()

    for a in data.get("alumnos", []):
        repo.alumnos[a["folio"]] = Alumno(
            folio=a["folio"], nombre=a.get("nombre", ""),
            apellido_paterno=a.get("apellido_paterno", ""),
            apellido_materno=a.get("apellido_materno", ""),
            grupo=a.get("grupo", ""), generacion=a.get("generacion", ""),
            correo=a.get("correo", ""),
        )

    for r in data.get("registros", []):
        tipo = r.get("tipo")
        try:
            fecha = datetime.fromisoformat(r["fecha_iso"]) if r.get("fecha_iso") else datetime.now()
        except Exception:
            fecha = datetime.now()

        if tipo == "prestamo":
            fecha_dev = None
            if r.get("Fecha_Devolucion"):
                try:
                    fecha_dev = datetime.strptime(r["Fecha_Devolucion"], "%d/%m/%Y %H:%M:%S")
                except Exception:
                    pass
            repo.registros.append(Prestamo(
                folio_alumno=r.get("Folio_Alumno", ""),
                estado=r.get("Estado", "Prestado"),
                fecha_devolucion=fecha_dev,
                datos_libro=r.get("Datos_Extraidos", ""),
                id_prestamo=r.get("ID_Prestamo"),
                fecha_hora=fecha,
                origen=r.get("Origen", "Manual"),
            ))
        elif tipo == "servicio":
            repo.registros.append(ServicioEstancia(
                tipo_servicio=r.get("Tipo_Servicio", "Otro"),
                folio_alumno=r.get("Folio_Alumno", ""),
                nombre_alumno=r.get("Nombre_Alumno", ""),
                grado=r.get("Grado", ""),
                grupo=r.get("Grupo", ""),
                responsable=r.get("Responsable", ""),
                cantidad_personas=int(r.get("Cantidad_Personas", 1)),
                fecha_hora=fecha,
                origen=r.get("Origen", "Estancia"),
            ))
    return True