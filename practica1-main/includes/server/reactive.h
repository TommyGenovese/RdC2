/**
 * @file reactive.h
 * @brief Fichero de cabecera para el módulo server/reactive, usado para la implementación de un servidor reactivo
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 26-02-2025
 */

#ifndef _REACTIVE_H
#define _REACTIVE_H

#include <string.h>

#include "server/start.h"
#include "server/utils.h"

/**
 * @struct react_args_t
 * @brief Estructura de datos que se utiliza para el procesamiento de peticiones en un servidor reactivo.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
typedef struct {
    p_process_func process; // La función que se utilizará para procesar cada petición.
    int connection_fd;      // El descriptor de la conexión con el cliente.
} react_args_t;

/**
 * @brief Lanza un hilo para que procese las peticiones de un cliente.
 *
 * @param process La función que se utilizará para procesar las peticiones.
 * @param socket_fd El descriptor del socket del que reciben peticiones.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return 0 si se lanza el hilo con éxito, -1 si hay algún error.
 */
int react_dispatch_thread(p_process_func process, int connection_fd);

#endif
