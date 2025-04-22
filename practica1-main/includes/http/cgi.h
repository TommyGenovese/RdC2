/**
 * @file cgi.h
 * @brief Fichero de cabecera para el módulo http/cgi, que se encarga de la ejecución de scripts.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 15-03-2025
 */

#ifndef _CGI_H
#define _CGI_H

#include <sys/time.h>
#include <sys/wait.h>

#include "config/config.h"
#include "logger/logger.h"
#include "server.h"

#define READ_END 0  // Extremo de lectura de un pipe
#define WRITE_END 1 // Extremo de escritura de un pipe

/**
 * @brief Concatena una string estática a otra dinámica.
 *
 * La cadena resultante también es memoria dinámica.
 * Si el puntero `orig` es `NULL`, equivale a una llamada a `strdup(src)`.
 *
 * Esta función modifica el puntero `orig`; en concreto, si no es `NULL` se
 * asume que es una cadena creada con memoria dinámica y en caso de éxito lo libera.
 *
 * @param orig La cadena dinámica original.
 * @param src La cadena estática que se quiere concatenar.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return Un nuevo puntero al resultado de la concatenación, o el puntero `orig`
 * si hay algún error.
 */
char *stradd(char *orig, const char *src);

/**
 * @brief Libera la memoria de un doble puntero generado por `parse_script_args`.
 *
 * @param args El puntero a liberar
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void args_free(void *args);

/**
 * @brief Obtiene los argumentos para un script de la URI.
 * 
 * Tras obtener la ruta completa, se debe llamar siempre a esta función, para detectar si se 
 * hace un request de una ejecución de un script o simplemente se solicita el envío de un archivo.
 * Además, en caso de ser un script con argumentos en la URI, esta función los parsea automáticamente.
 * 
 * Entre los argumentos se incluye el intérprete que se debe usar y la ruta del script, por lo que solo
 * hace falta determinar si el verbo que se ha usado es GET (se usa `cgi_get_script`) o POST (se usa
 * `cgi_post_script`).
 *
 * Si no es `NULL`, el puntero retornado se debe liberar después con `args_free`.
 *
 * @param path La ruta completa (root + URI) de la que extraer los argumentos
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * 
 * @return `NULL` si no se trata de un script. Si es un script, un array de strings
 * finalizada en puntero `NULL`, que contiene como primer argumento la ruta del intérprete,
 * como segundo la ruta completa del script, y después el resto de argumentos de la URI (si los hay).
 */
char **parse_script_args(char *path);

/**
 * @brief Ejecuta un script solicitado con GET (sin argumentos en el cuerpo).
 * 
 * Si no es `NULL`, el puntero retornado se debe liberar después con `free`.
 * 
 * @param argv El array de argumentos leídos de la URI con `parse_script_args`.
 * @param connection_fd El descriptor de la conexión con el cliente.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * 
 * @return La respuesta que el script ha emitido por su salida estándar, en forma 
 * string dinámica; o `NULL` si hay algún error.
 */
char *cgi_get_script(char *const *argv, int connection_fd);

/**
 * @brief Ejecuta un script solicitado con POST (con argumentos en el cuerpo).
 * 
 * Si no es `NULL`, el puntero retornado se debe liberar después con `free`.
 * 
 * @param argv El array de argumentos leídos de la URI con `parse_script_args`.
 * @param connection_fd El descriptor de la conexión con el cliente.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * 
 * @return La respuesta que el script ha emitido por su salida estándar, en forma 
 * string dinámica; o `NULL` si hay algún error.
 */
char *cgi_post_script(char *const *argv, int connection_fd);

#endif