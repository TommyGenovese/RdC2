/**
 * @file start.h
 * @brief Fichero de cabecera para el módulo server/start, con funciones para abrir un socket y aceptar una conexión
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 01-03-2025
 */

#ifndef _START_H
#define _START_H

#include <errno.h>
#include <netinet/in.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#include "logger/logger.h"

#define PORT 8080      // Puerto por defecto por el que se conectarán los clientes
#define BUFF_SIZE 4096 // Tamaño del búfer de lectura/escritura

extern int socket_fd; // Variable global para el descriptor del socket del servidor

typedef void (*p_process_func)(int); // Tipo de función aceptado para el procesamiento de peticiones

/**
 * @brief Función de cierre del socket del servidor para llamar al cerrar el servidor
 * escrita en el formato requerido por la función `atexit`.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void cleanup_socket_fd(void);

/**
 * @brief Abre el puerto `port` y se queda escuchando para recibir clientes.
 *
 * @param port El puerto que se quiere abrir para recibir clientes.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return El descriptor de fichero para el socket, o -1 si hay algún error.
 */
int get_server_socket(int port);

/**
 * @brief Acepta un cliente del socket.
 *
 * @param socket_fd Descriptor de fichero del socket por el que se recibe el cliente.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return El descriptor de fichero para la conexión, o -1 si hay algún error.
 */
int get_client_from_socket(int socket_fd);

/**
 * @brief Función sencilla que realiza un ping con los mensajes que recibe del cliente
 * en el formato especificado por `p_process_func`.
 *
 * @param connection_fd Descriptor de la conexión con el cliente.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
void ping(int connection_fd);

#endif