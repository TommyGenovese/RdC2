/**
 * @file pool.h
 * @brief Fichero de cabecera para el módulo server/pool, usado para la implementación de un servidor
 * con pool de hilos
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 26-02-2025
 */

#ifndef _POOL_H
#define _POOL_H

#include <string.h>

#include "server/start.h"
#include "server/utils.h"

/**
 * @struct pool_args_t
 * @brief Estructura de datos que se utiliza para el procesamiento de peticiones con pool de hilos.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
typedef struct {
    p_process_func process; // La función que se utilizará para procesar cada petición.
    int socket_fd;          // El descriptor del socket del que se aceptan conexiones.
} pool_args_t;

/**
 * @brief Lanza los hilos en un servidor con pool de hilos.
 *
 * @param process La función que se utilizará para procesar las peticiones.
 * @param socket_fd El descriptor del socket del que se aceptan conexiones.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return 0 si se lanzan los hilos con éxito, -1 si hay algún error.
 */
int pool_dispatch_threads(p_process_func process, int socket_fd);

/**
 * @brief Suspende el hilo principal hasta que recibe `SIGINT`.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void pool_main_suspend(void);

#endif