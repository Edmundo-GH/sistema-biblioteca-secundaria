import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

// 1. ENTIDADES
class Alumno {
    private String folio, nombreCompleto, grado, grupo;
    public Alumno(String folio, String nombreCompleto, String grado, String grupo) {
        this.folio = folio; 
        this.nombreCompleto = nombreCompleto; 
        this.grado = grado; 
        this.grupo = grupo;
    }
    public String getFolio() { return folio; }
    public String getNombre() { return nombreCompleto; }
    public String getGrado() { return grado; }
    public String getGrupo() { return grupo; }
    
    public String getGradoGrupo() { 
        String g = (grado.trim() + grupo.trim()).toUpperCase();
        return g.replace(" ", "").replace("-", ""); 
    }
}

class Prestamo {
    private String folioAlumno, estado, fechaSalida;
    public Prestamo(String folioAlumno, String estado, String fechaSalida) {
        this.folioAlumno = folioAlumno;
        this.estado = estado;
        this.fechaSalida = fechaSalida;
    }
    public String getFolioAlumno() { return folioAlumno; }
    public String getEstado() { return estado; }
    public String getMesRegistro() {
        if (fechaSalida == null || fechaSalida.trim().isEmpty()) return "Desconocido";
        try {
            String soloFecha = fechaSalida.split(" ")[0]; 
            String[] partes = soloFecha.split("[-/]"); 
            if (partes.length >= 3) {
                if (partes[0].length() == 4) return partes[1] + "/" + partes[0];
                else return partes[1] + "/" + partes[2];
            }
        } catch (Exception e) { return "Error_Fecha"; }
        return "Desconocido";
    }
}

// 2. MOTOR
class AnaliticaBiblioteca {
    private Map<String, Alumno> padron = new HashMap<>();
    private List<Prestamo> historial = new ArrayList<>();

    private String detectarSeparador(String linea) {
        if (linea.contains(";")) return ";";
        if (linea.contains("\t")) return "\t";
        return ",";
    }

    private String limpiarDato(String dato) {
        if (dato == null) return "";
        String limpio = dato.replace("\uFEFF", "").replace("\"", "").trim();
        if (limpio.endsWith(".0")) return limpio.substring(0, limpio.length() - 2); 
        return limpio;
    }

    private int encontrarColumna(String[] encabezados, String... posiblesNombres) {
        for (int i = 0; i < encabezados.length; i++) {
            String col = limpiarDato(encabezados[i]).toUpperCase();
            for (String nom : posiblesNombres) {
                if (col.equals(nom) || col.contains(nom)) return i;
            }
        }
        return -1;
    }

    // CALCULA EL GRADO DESDE LA GENERACIÓN PARA EL CICLO 2026
    private String calcularGrado(String generacion) {
        if (generacion == null || generacion.isEmpty()) return "?";
        String str = generacion.replaceAll("[^0-9]", " ");
        
        // try-with-resources cierra el Scanner automáticamente al terminar
        try (Scanner sc = new Scanner(str)) {
            while(sc.hasNextInt()) {
                int year = sc.nextInt();
                if (year == 2026 || year == 2029) return "1"; // Inicia 2026 o se gradúa 2029
                if (year == 2025 || year == 2028) return "2"; // Inicia 2025 o se gradúa 2028
                if (year == 2024 || year == 2027) return "3"; // Inicia 2024 o se gradúa 2027
            }
        }
        return "?";
    }

    public void cargarDatos(String rutaAlumnos, String rutaPrestamos) {
        try (BufferedReader br = new BufferedReader(new FileReader(rutaAlumnos))) {
            String header = br.readLine();
            if (header != null) {
                String sep = detectarSeparador(header);
                String[] enc = header.split(sep);
                
                int colFolio = encontrarColumna(enc, "FOLIO", "MATRICULA", "ID");
                int colNombre = encontrarColumna(enc, "NOMBRE", "NOMBRES");
                int colPaterno = encontrarColumna(enc, "PATERNO", "APELLIDO 1", "APELLIDO PATERNO");
                int colMaterno = encontrarColumna(enc, "MATERNO", "APELLIDO 2", "APELLIDO MATERNO");
                int colGrado = encontrarColumna(enc, "GRADO");
                int colGeneracion = encontrarColumna(enc, "GENERACION", "GENERACIÓN");
                int colGrupo = encontrarColumna(enc, "GRUPO");

                if (colFolio == -1) colFolio = 0;

                String linea;
                while ((linea = br.readLine()) != null) {
                    if (linea.trim().isEmpty()) continue;
                    String[] d = linea.split(sep);
                    if (d.length > colFolio) {
                        String folio = limpiarDato(d[colFolio]);
                        
                        // UNE PATERNO, MATERNO Y NOMBRES
                        String nombreFinal = "";
                        if (colPaterno != -1 && d.length > colPaterno) nombreFinal += limpiarDato(d[colPaterno]) + " ";
                        if (colMaterno != -1 && d.length > colMaterno) nombreFinal += limpiarDato(d[colMaterno]) + " ";
                        if (colNombre != -1 && d.length > colNombre) nombreFinal += limpiarDato(d[colNombre]);
                        nombreFinal = nombreFinal.trim();
                        if (nombreFinal.isEmpty() && d.length > 1) nombreFinal = limpiarDato(d[1]);

                        // ASIGNA EL GRADO
                        String grado = "";
                        if (colGrado != -1 && d.length > colGrado) {
                            grado = limpiarDato(d[colGrado]);
                        } else if (colGeneracion != -1 && d.length > colGeneracion) {
                            grado = calcularGrado(limpiarDato(d[colGeneracion]));
                        }
                        
                        String grupo = (colGrupo != -1 && d.length > colGrupo) ? limpiarDato(d[colGrupo]) : "";
                        padron.put(folio, new Alumno(folio, nombreFinal, grado, grupo));
                    }
                }
            }
        } catch (Exception e) { System.out.println("Error padrón: " + e.getMessage()); }

        try (BufferedReader br = new BufferedReader(new FileReader(rutaPrestamos))) {
            String header = br.readLine();
            if (header != null) {
                String sep = detectarSeparador(header);
                String[] enc = header.split(sep);
                
                int colFolio = encontrarColumna(enc, "FOLIO", "ALUMNO");
                int colFecha = encontrarColumna(enc, "FECHA_SALIDA", "FECHA", "SALIDA");
                int colEstado = encontrarColumna(enc, "ESTADO", "STATUS");
                
                if (colFolio == -1) colFolio = 1;
                if (colFecha == -1) colFecha = 2;
                if (colEstado == -1) colEstado = 5;

                String linea;
                while ((linea = br.readLine()) != null) {
                    if (linea.trim().isEmpty()) continue;
                    String[] d = linea.split(sep + "(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)");
                    if (d.length > colFolio) {
                        String folio = limpiarDato(d[colFolio]);
                        String fecha = d.length > colFecha ? limpiarDato(d[colFecha]) : "";
                        String estado = d.length > colEstado ? limpiarDato(d[colEstado]) : "";
                        historial.add(new Prestamo(folio, estado, fecha));
                    }
                }
            }
        } catch (Exception e) { System.out.println("Error AppSheet: " + e.getMessage()); }
    }

    public void generarReportesArchivos() {
        if (padron.isEmpty() || historial.isEmpty()) return;
        exportarDeudores();
        exportarEstadisticas();
    }

    private void exportarDeudores() {
        List<Alumno> deudores = new ArrayList<>();
        for (Prestamo p : historial) {
            if (p.getEstado().toUpperCase().contains("PRESTADO")) {
                Alumno a = padron.get(p.getFolioAlumno());
                if (a != null) deudores.add(a);
            }
        }
        
        deudores.sort(Comparator.comparing(Alumno::getGrado).thenComparing(Alumno::getGrupo).thenComparing(Alumno::getNombre));

        try (PrintWriter writer = new PrintWriter(new FileWriter("Reporte_Deudores.csv"))) {
            writer.println("Grado,Grupo,Nombre_Completo,Folio");
            for (Alumno a : deudores) {
                writer.printf("%s,%s,%s,%s\n", a.getGrado(), a.getGrupo(), a.getNombre(), a.getFolio());
            }
        } catch (Exception e) { }
    }

    private void exportarEstadisticas() {
        Map<String, Integer> indiceMensual = new HashMap<>();
        Map<String, Integer> lecturasPorGrupo = new HashMap<>();
        Map<String, Integer> lecturasPorAlumno = new HashMap<>();
        Map<String, Alumno> datosAlumnosTop = new HashMap<>();

        for (Prestamo p : historial) {
            indiceMensual.put(p.getMesRegistro(), indiceMensual.getOrDefault(p.getMesRegistro(), 0) + 1);
            Alumno a = padron.get(p.getFolioAlumno());
            if (a != null) {
                String gg = a.getGradoGrupo();
                lecturasPorGrupo.put(gg, lecturasPorGrupo.getOrDefault(gg, 0) + 1);
                
                int librosLeidos = lecturasPorAlumno.getOrDefault(a.getFolio(), 0) + 1;
                lecturasPorAlumno.put(a.getFolio(), librosLeidos);
                datosAlumnosTop.put(a.getFolio(), a);
            }
        }

        double totalAlumnos = padron.size();
        double indiceLectorTotal = totalAlumnos > 0 ? (double) historial.size() / totalAlumnos : 0;

        try (PrintWriter writer = new PrintWriter(new FileWriter("Reporte_Estadisticas.csv"))) {
            
            writer.println("=== INDICE LECTOR ===");
            writer.printf("Total de Alumnos matriculados:,%.0f\n", totalAlumnos);
            writer.printf("Total de Libros Prestados:,%d\n", historial.size());
            writer.printf("INDICE LECTOR TOTAL (Promedio de libros por alumno):,%.4f\n", indiceLectorTotal);
            
            writer.println("\n=== INDICE LECTOR POR MES ===");
            writer.println("Mes,Libros_Leidos,Indice_Mensual");
            for (Map.Entry<String, Integer> entry : indiceMensual.entrySet()) {
                double indiceMes = totalAlumnos > 0 ? (double) entry.getValue() / totalAlumnos : 0;
                writer.printf("%s,%d,%.4f\n", entry.getKey(), entry.getValue(), indiceMes);
            }

            writer.println("\n=== LECTURAS TOTALES POR GRUPO ===");
            writer.println("Grupo,Total_Libros_Leidos");
            String[] todosLosGrupos = {
                "1A", "1B", "1C", "1D", "1E", "1F",
                "2A", "2B", "2C", "2D", "2E", "2F",
                "3A", "3B", "3C", "3D", "3E", "3F"
            };
            for (String g : todosLosGrupos) {
                writer.printf("%s,%d\n", g, lecturasPorGrupo.getOrDefault(g, 0));
            }

            writer.println("\n=== TOP 10 ALUMNOS LECTORES ===");
            writer.println("Grado,Grupo,Nombre_Completo,Libros_Leidos");
            lecturasPorAlumno.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(10)
                .forEach(e -> {
                    Alumno a = datosAlumnosTop.get(e.getKey());
                    writer.printf("%s,%s,%s,%d\n", a.getGrado(), a.getGrupo(), a.getNombre(), e.getValue());
                });
                
        } catch (Exception e) { }
    }
}

public class Main {
    public static void main(String[] args) {
        AnaliticaBiblioteca motor = new AnaliticaBiblioteca();
        motor.cargarDatos("BD_NORMALIZADA_EJEMPLO.csv", "Registro_Biblioteca_EJEMPLO.csv");
        motor.generarReportesArchivos();
    }
}