```java
// Importa las clases necesarias para leer y escribir archivos de texto.
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

// ============================================================
// 1. ENTIDADES
// ============================================================

// Clase que representa a un alumno dentro del sistema.
class Alumno {

    // Atributos que almacenan la información básica del alumno.
    private String folio, nombreCompleto, grado, grupo;

    // Constructor de la clase Alumno.
    // Recibe los datos iniciales y los asigna a sus atributos.
    public Alumno(String folio, String nombreCompleto, String grado, String grupo) {
        this.folio = folio; 
        this.nombreCompleto = nombreCompleto; 
        this.grado = grado; 
        this.grupo = grupo;
    }

    // Métodos getter para consultar los datos del alumno.
    public String getFolio() { return folio; }
    public String getNombre() { return nombreCompleto; }
    public String getGrado() { return grado; }
    public String getGrupo() { return grupo; }
    
    // Obtiene el grado y grupo en un formato uniforme.
    // Elimina espacios y guiones y convierte el texto a mayúsculas.
    public String getGradoGrupo() { 
        String g = (grado.trim() + grupo.trim()).toUpperCase();
        return g.replace(" ", "").replace("-", ""); 
    }
}


// Clase que representa un préstamo realizado por un alumno.
class Prestamo {

    // Atributos que almacenan la información del préstamo.
    private String folioAlumno, estado, fechaSalida;

    // Constructor de la clase Prestamo.
    // Recibe los datos del préstamo y los asigna a sus atributos.
    public Prestamo(String folioAlumno, String estado, String fechaSalida) {
        this.folioAlumno = folioAlumno;
        this.estado = estado;
        this.fechaSalida = fechaSalida;
    }

    // Métodos getter para consultar los datos del préstamo.
    public String getFolioAlumno() { return folioAlumno; }
    public String getEstado() { return estado; }

    // Obtiene el mes y año correspondiente a la fecha del préstamo.
    public String getMesRegistro() {

        // Si no existe una fecha válida, devuelve "Desconocido".
        if (fechaSalida == null || fechaSalida.trim().isEmpty()) return "Desconocido";

        try {

            // Separa la fecha de cualquier información adicional de hora.
            String soloFecha = fechaSalida.split(" ")[0]; 

            // Separa las diferentes partes de la fecha.
            String[] partes = soloFecha.split("[-/]"); 

            // Verifica que la fecha tenga al menos tres partes.
            if (partes.length >= 3) {

                // Si el primer elemento tiene cuatro caracteres,
                // se interpreta como el año.
                if (partes[0].length() == 4) return partes[1] + "/" + partes[0];

                // De lo contrario, se interpreta como día/mes/año.
                else return partes[1] + "/" + partes[2];
            }

        // Si ocurre algún problema al procesar la fecha,
        // devuelve un mensaje de error.
        } catch (Exception e) { return "Error_Fecha"; }

        return "Desconocido";
    }
}


// ============================================================
// 2. MOTOR
// ============================================================

// Clase principal encargada de cargar, procesar y analizar
// la información de alumnos y préstamos.
class AnaliticaBiblioteca {

    // Almacena los alumnos utilizando su folio como clave.
    private Map<String, Alumno> padron = new HashMap<>();

    // Almacena todos los registros de préstamos.
    private List<Prestamo> historial = new ArrayList<>();

    // Detecta automáticamente qué separador utiliza el archivo.
    private String detectarSeparador(String linea) {

        // Si encuentra punto y coma, utiliza ese separador.
        if (linea.contains(";")) return ";";

        // Si encuentra tabulaciones, utiliza tabulación.
        if (linea.contains("\t")) return "\t";

        // En caso contrario, utiliza coma.
        return ",";
    }


    // Limpia y normaliza un dato obtenido del archivo.
    private String limpiarDato(String dato) {

        // Si el dato es nulo, devuelve una cadena vacía.
        if (dato == null) return "";

        // Elimina caracteres especiales, comillas y espacios.
        String limpio = dato.replace("\uFEFF", "").replace("\"", "").trim();

        // Si el dato termina en ".0", elimina esa parte.
        if (limpio.endsWith(".0")) return limpio.substring(0, limpio.length() - 2); 

        return limpio;
    }


    // Busca la posición de una columna utilizando diferentes nombres posibles.
    private int encontrarColumna(String[] encabezados, String... posiblesNombres) {

        // Recorre todos los encabezados del archivo.
        for (int i = 0; i < encabezados.length; i++) {

            // Limpia el encabezado y lo convierte a mayúsculas.
            String col = limpiarDato(encabezados[i]).toUpperCase();

            // Compara el encabezado con los nombres posibles.
            for (String nom : posiblesNombres) {

                // Devuelve la posición cuando encuentra coincidencia.
                if (col.equals(nom) || col.contains(nom)) return i;
            }
        }

        // Si no encuentra la columna, devuelve -1.
        return -1;
    }


    // Calcula el grado del alumno a partir de su generación
    // considerando el ciclo escolar 2026.
    private String calcularGrado(String generacion) {

        // Si no existe información de generación, devuelve "?".
        if (generacion == null || generacion.isEmpty()) return "?";

        // Conserva únicamente los números de la generación.
        String str = generacion.replaceAll("[^0-9]", " ");
        
        // try-with-resources cierra el Scanner automáticamente al terminar.
        try (Scanner sc = new Scanner(str)) {

            // Revisa cada año encontrado en la generación.
            while(sc.hasNextInt()) {
                int year = sc.nextInt();

                // Inicia 2026 o se gradúa en 2029: primer grado.
                if (year == 2026 || year == 2029) return "1";

                // Inicia 2025 o se gradúa en 2028: segundo grado.
                if (year == 2025 || year == 2028) return "2";

                // Inicia 2024 o se gradúa en 2027: tercer grado.
                if (year == 2024 || year == 2027) return "3";
            }
        }

        // Si no se puede determinar el grado, devuelve "?".
        return "?";
    }


    // Carga la información de alumnos y préstamos desde archivos CSV.
    public void cargarDatos(String rutaAlumnos, String rutaPrestamos) {

        // ========================================================
        // CARGA DEL PADRÓN DE ALUMNOS
        // ========================================================

        // Abre el archivo de alumnos para lectura.
        try (BufferedReader br = new BufferedReader(new FileReader(rutaAlumnos))) {

            // Lee la primera línea, que contiene los encabezados.
            String header = br.readLine();

            if (header != null) {

                // Detecta el separador utilizado en el archivo.
                String sep = detectarSeparador(header);

                // Divide los encabezados en columnas.
                String[] enc = header.split(sep);
                
                // Identifica las posiciones de las diferentes columnas.
                int colFolio = encontrarColumna(enc, "FOLIO", "MATRICULA", "ID");
                int colNombre = encontrarColumna(enc, "NOMBRE", "NOMBRES");
                int colPaterno = encontrarColumna(enc, "PATERNO", "APELLIDO 1", "APELLIDO PATERNO");
                int colMaterno = encontrarColumna(enc, "MATERNO", "APELLIDO 2", "APELLIDO MATERNO");
                int colGrado = encontrarColumna(enc, "GRADO");
                int colGeneracion = encontrarColumna(enc, "GENERACION", "GENERACIÓN");
                int colGrupo = encontrarColumna(enc, "GRUPO");

                // Si no encuentra la columna de folio,
                // utiliza la primera columna como referencia.
                if (colFolio == -1) colFolio = 0;

                String linea;

                // Lee el archivo línea por línea.
                while ((linea = br.readLine()) != null) {

                    // Ignora las líneas vacías.
                    if (linea.trim().isEmpty()) continue;

                    // Divide la línea en sus diferentes columnas.
                    String[] d = linea.split(sep);

                    if (d.length > colFolio) {

                        // Obtiene y limpia el folio del alumno.
                        String folio = limpiarDato(d[colFolio]);
                        
                        // UNE PATERNO, MATERNO Y NOMBRES
                        String nombreFinal = "";

                        // Agrega el apellido paterno.
                        if (colPaterno != -1 && d.length > colPaterno) nombreFinal += limpiarDato(d[colPaterno]) + " ";

                        // Agrega el apellido materno.
                        if (colMaterno != -1 && d.length > colMaterno) nombreFinal += limpiarDato(d[colMaterno]) + " ";

                        // Agrega el nombre.
                        if (colNombre != -1 && d.length > colNombre) nombreFinal += limpiarDato(d[colNombre]);

                        // Elimina espacios innecesarios al inicio y final.
                        nombreFinal = nombreFinal.trim();

                        // Si no pudo construir el nombre, utiliza la segunda columna.
                        if (nombreFinal.isEmpty() && d.length > 1) nombreFinal = limpiarDato(d[1]);

                        // ASIGNA EL GRADO
                        String grado = "";

                        // Si existe una columna de grado, utiliza ese dato.
                        if (colGrado != -1 && d.length > colGrado) {
                            grado = limpiarDato(d[colGrado]);

                        // Si no existe grado, intenta calcularlo mediante la generación.
                        } else if (colGeneracion != -1 && d.length > colGeneracion) {
                            grado = calcularGrado(limpiarDato(d[colGeneracion]));
                        }
                        
                        // Obtiene el grupo del alumno si existe.
                        String grupo = (colGrupo != -1 && d.length > colGrupo) ? limpiarDato(d[colGrupo]) : "";

                        // Crea un objeto Alumno y lo almacena en el padrón usando el folio.
                        padron.put(folio, new Alumno(folio, nombreFinal, grado, grupo));
                    }
                }
            }

        // Muestra el mensaje correspondiente si ocurre un error al cargar el padrón.
        } catch (Exception e) { System.out.println("Error padrón: " + e.getMessage()); }


        // ========================================================
        // CARGA DEL HISTORIAL DE PRÉSTAMOS
        // ========================================================

        // Abre el archivo de préstamos para lectura.
        try (BufferedReader br = new BufferedReader(new FileReader(rutaPrestamos))) {

            // Lee los encabezados del archivo.
            String header = br.readLine();

            if (header != null) {

                // Detecta el separador utilizado.
                String sep = detectarSeparador(header);

                // Divide los encabezados en columnas.
                String[] enc = header.split(sep);
                
                // Identifica las columnas necesarias del archivo de préstamos.
                int colFolio = encontrarColumna(enc, "FOLIO", "ALUMNO");
                int colFecha = encontrarColumna(enc, "FECHA_SALIDA", "FECHA", "SALIDA");
                int colEstado = encontrarColumna(enc, "ESTADO", "STATUS");
                
                // Utiliza posiciones predeterminadas si no encuentra los encabezados.
                if (colFolio == -1) colFolio = 1;
                if (colFecha == -1) colFecha = 2;
                if (colEstado == -1) colEstado = 5;

                String linea;

                // Lee cada registro del archivo de préstamos.
                while ((linea = br.readLine()) != null) {

                    // Ignora líneas vacías.
                    if (linea.trim().isEmpty()) continue;

                    // Divide la línea respetando los valores entre comillas.
                    String[] d = linea.split(sep + "(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)");

                    if (d.length > colFolio) {

                        // Obtiene y limpia los datos del préstamo.
                        String folio = limpiarDato(d[colFolio]);
                        String fecha = d.length > colFecha ? limpiarDato(d[colFecha]) : "";
                        String estado = d.length > colEstado ? limpiarDato(d[colEstado]) : "";

                        // Crea un objeto Prestamo y lo agrega al historial.
                        historial.add(new Prestamo(folio, estado, fecha));
                    }
                }
            }

        // Muestra el mensaje correspondiente si ocurre un error al cargar los préstamos.
        } catch (Exception e) { System.out.println("Error AppSheet: " + e.getMessage()); }
    }


    // Genera los diferentes reportes del sistema.
    public void generarReportesArchivos() {

        // Si no hay alumnos o préstamos, no genera reportes.
        if (padron.isEmpty() || historial.isEmpty()) return;

        // Genera el reporte de alumnos con préstamos pendientes.
        exportarDeudores();

        // Genera el reporte de estadísticas de lectura.
        exportarEstadisticas();
    }


    // ============================================================
    // REPORTE DE ALUMNOS CON PRÉSTAMOS PENDIENTES
    // ============================================================

    // Identifica y exporta los alumnos que tienen préstamos registrados.
    private void exportarDeudores() {

        // Lista donde se almacenarán los alumnos identificados.
        List<Alumno> deudores = new ArrayList<>();

        // Recorre todo el historial de préstamos.
        for (Prestamo p : historial) {

            // Comprueba si el estado del préstamo contiene "PRESTADO".
            if (p.getEstado().toUpperCase().contains("PRESTADO")) {

                // Busca al alumno correspondiente mediante su folio.
                Alumno a = padron.get(p.getFolioAlumno());

                // Si encuentra al alumno, lo agrega a la lista.
                if (a != null) deudores.add(a);
            }
        }
        
        // Ordena los alumnos por grado, grupo y nombre.
        deudores.sort(Comparator.comparing(Alumno::getGrado).thenComparing(Alumno::getGrupo).thenComparing(Alumno::getNombre));

        // Crea el archivo CSV del reporte de deudores.
        try (PrintWriter writer = new PrintWriter(new FileWriter("Reporte_Deudores.csv"))) {

            // Escribe los encabezados del reporte.
            writer.println("Grado,Grupo,Nombre_Completo,Folio");

            // Recorre la lista de alumnos identificados.
            for (Alumno a : deudores) {

                // Escribe los datos del alumno en el archivo.
                writer.printf("%s,%s,%s,%s\n", a.getGrado(), a.getGrupo(), a.getNombre(), a.getFolio());
            }

        } catch (Exception e) { }
    }


    // ============================================================
    // REPORTE DE ESTADÍSTICAS
    // ============================================================

    // Calcula y exporta las estadísticas de lectura.
    private void exportarEstadisticas() {

        // Almacena el número de lecturas realizadas por mes.
        Map<String, Integer> indiceMensual = new HashMap<>();

        // Almacena el total de lecturas realizadas por grupo.
        Map<String, Integer> lecturasPorGrupo = new HashMap<>();

        // Almacena el total de libros leídos por cada alumno.
        Map<String, Integer> lecturasPorAlumno = new HashMap<>();

        // Guarda los datos de los alumnos que aparecen en el ranking.
        Map<String, Alumno> datosAlumnosTop = new HashMap<>();

        // Recorre todos los préstamos registrados.
        for (Prestamo p : historial) {

            // Cuenta los préstamos realizados en cada mes.
            indiceMensual.put(p.getMesRegistro(), indiceMensual.getOrDefault(p.getMesRegistro(), 0) + 1);

            // Busca al alumno relacionado con el préstamo.
            Alumno a = padron.get(p.getFolioAlumno());

            if (a != null) {

                // Obtiene el grado y grupo del alumno.
                String gg = a.getGradoGrupo();

                // Incrementa el contador de lecturas del grupo.
                lecturasPorGrupo.put(gg, lecturasPorGrupo.getOrDefault(gg, 0) + 1);
                
                // Obtiene el número actual de libros leídos por el alumno
                // y agrega uno por el préstamo actual.
                int librosLeidos = lecturasPorAlumno.getOrDefault(a.getFolio(), 0) + 1;

                // Guarda el nuevo total de libros leídos.
                lecturasPorAlumno.put(a.getFolio(), librosLeidos);

                // Guarda los datos del alumno para utilizarlos posteriormente.
                datosAlumnosTop.put(a.getFolio(), a);
            }
        }

        // Obtiene el número total de alumnos registrados.
        double totalAlumnos = padron.size();

        // Calcula el promedio de libros prestados por alumno.
        double indiceLectorTotal = totalAlumnos > 0 ? (double) historial.size() / totalAlumnos : 0;

        // Crea el archivo CSV donde se guardarán las estadísticas.
        try (PrintWriter writer = new PrintWriter(new FileWriter("Reporte_Estadisticas.csv"))) {
            
            // ====================================================
            // ÍNDICE LECTOR GENERAL
            // ====================================================

            writer.println("=== INDICE LECTOR ===");

            // Escribe el total de alumnos matriculados.
            writer.printf("Total de Alumnos matriculados:,%.0f\n", totalAlumnos);

            // Escribe el total de libros prestados.
            writer.printf("Total de Libros Prestados:,%d\n", historial.size());

            // Escribe el promedio de libros por alumno.
            writer.printf("INDICE LECTOR TOTAL (Promedio de libros por alumno):,%.4f\n", indiceLectorTotal);
            
            // ====================================================
            // ÍNDICE LECTOR POR MES
            // ====================================================

            writer.println("\n=== INDICE LECTOR POR MES ===");
            writer.println("Mes,Libros_Leidos,Indice_Mensual");

            // Recorre las estadísticas mensuales y calcula el índice de cada mes.
            for (Map.Entry<String, Integer> entry : indiceMensual.entrySet()) {

                // Calcula el promedio mensual de libros por alumno.
                double indiceMes = totalAlumnos > 0 ? (double) entry.getValue() / totalAlumnos : 0;

                // Escribe los resultados del mes en el archivo.
                writer.printf("%s,%d,%.4f\n", entry.getKey(), entry.getValue(), indiceMes);
            }


            // ====================================================
            // LECTURAS TOTALES POR GRUPO
            // ====================================================

            writer.println("\n=== LECTURAS TOTALES POR GRUPO ===");
            writer.println("Grupo,Total_Libros_Leidos");

            // Lista de los grupos considerados por el sistema.
            String[] todosLosGrupos = {
                "1A", "1B", "1C", "1D", "1E", "1F",
                "2A", "2B", "2C", "2D", "2E", "2F",
                "3A", "3B", "3C", "3D", "3E", "3F"
            };

            // Recorre todos los grupos para generar su total de lecturas.
            for (String g : todosLosGrupos) {

                // Si un grupo no tiene lecturas, se registra como cero.
                writer.printf("%s,%d\n", g, lecturasPorGrupo.getOrDefault(g, 0));
            }


            // ====================================================
            // TOP 10 ALUMNOS LECTORES
            // ====================================================

            writer.println("\n=== TOP 10 ALUMNOS LECTORES ===");
            writer.println("Grado,Grupo,Nombre_Completo,Libros_Leidos");

            // Ordena a los alumnos de mayor a menor cantidad de libros
            // y limita el resultado a los primeros diez.
            lecturasPorAlumno.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(10)
                .forEach(e -> {

                    // Recupera los datos completos del alumno.
                    Alumno a = datosAlumnosTop.get(e.getKey());

                    // Escribe la información del alumno en el reporte.
                    writer.printf("%s,%s,%s,%d\n", a.getGrado(), a.getGrupo(), a.getNombre(), e.getValue());
                });
                
        } catch (Exception e) { }
    }
}


// ============================================================
// 3. PROGRAMA PRINCIPAL
// ============================================================

// Clase principal desde donde comienza la ejecución del programa.
public class Main {

    // Método principal de Java.
    // Es el punto de entrada de la aplicación.
    public static void main(String[] args) {

        // Crea una instancia del motor de análisis de la biblioteca.
        AnaliticaBiblioteca motor = new AnaliticaBiblioteca();

        // Carga el padrón de alumnos y el historial de préstamos
        // utilizando los archivos CSV de ejemplo.
        motor.cargarDatos("BD_NORMALIZADA_EJEMPLO.csv", "Registro_Biblioteca_EJEMPLO.csv");

        // Procesa la información y genera los archivos de reportes.
        motor.generarReportesArchivos();
    }
}
```
