/**
 * @file config.h
 * @brief Fichero de cabecera para el módulo config, que se encarga de la configuración.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 11-03-2025
 */

#ifndef _CONFIG_H
#define _CONFIG_H

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "server.h"

#define MAX_FULL_PATH 4096 // Convención para máxima longitud de ruta en Linux
#define FNAME_SIZE 12      // Longitud de la cadena "server.conf"

/**
 * @struct config_t
 * @brief Estructura de datos que se utiliza para almacenar la configuración.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
typedef struct {
    char config_dir[MAX_FULL_PATH];                   // Ruta del directorio del archivo server.conf
    char config_path[MAX_FULL_PATH + FNAME_SIZE + 1]; // Ruta de server.conf
    char *server_root;                                // Ruta del directorio raíz del servidor web
    char *server_signature;                           // Nombre del servidor
    int max_clients;                                  // Máximo de clientes aceptados (máximo de hilos)
    int listen_port;                                  // Puerto de escucha
    server_mode_t server_mode;                        // Modo en que opera el servidor: pool/reactive/iterative
    char *logger_path;                                // Ruta del fichero de loggeo
} config_t;

extern config_t config; // Configuración que usará el servidor

/**
 * @brief Función de liberación de los recursos de configuración,
 * en el formato requerido por `atexit`.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void config_cleanup(void);

/**
 * @brief Lee el fichero de configuración y almacena los datos.
 *
 * El fichero de configuración se busca en el directorio en el que está el
 * ejecutable, y siempre se llama server.conf.
 *
 * Si no se encuentra el fichero, esta función falla.
 *
 * Si en el fichero no se definen valores para server_root, server_signature o
 * logger_path, esta función falla. Además, se utilizarán valores sin espacios
 * para estas cadenas.
 *
 * Por defecto, se inicializa el máximo de clientes a 1, el modo a ITERATIVE y el
 * puerto a PORT (definido en server/start.h).
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se guarda una configuración adecuada, -1 en caso de error
 */
int config_start();

/**
 * @brief Función que guarda los valores leídos de server.conf en el fichero
 * indicado.
 *
 * Si el fichero ya existe, borra su contenido para escribir los datos.
 * Si no, lo crea.
 *
 * @param filename El nombre del fichero donde se guardará la configuración
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void config_dump(char *filename);

#endif
