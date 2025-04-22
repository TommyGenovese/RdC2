/**
 * @file reactive.c
 * @brief Fichero de implementación del módulo server/reactive, usado para la implementación de un servidor reactivo
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 01-03-2025
 */

#include "server/reactive.h"

static react_args_t args = {.connection_fd = -1, .process = NULL};

/**
 * @brief Función que cierra el descriptor de la conexión con el cliente,
 * en el formato requerido por `pthread_cleanup_push`.
 *
 * @param args Puntero al descriptor de la conexión
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void react_cleanup_fd(void *args) {
    int connection_fd;
    connection_fd = *(int *)args;
    close(connection_fd);
    log_info("Connection closed.");
}

/**
 * @brief Función que elimina la ID del hilo de la tabla en el formato requerido
 * por `pthread_cleanup_push`.
 *
 * @param args Puntero a los argumentos, en este caso no se utiliza
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void react_child_cleanup(__attribute__((unused)) void *args) {
    int i;

    sem_wait(mutex);
    for (i = 0; i < n_threads; i++) {
        if (threads[i] == pthread_self()) {
            break;
        }
    }
    n_threads--;
    if (i < n_threads) {
        memmove((void *)(threads + i), (const void *)(threads + i + 1),
                sizeof(pthread_t) * (n_threads - i));
    }
    sem_post(mutex);
    sem_post(barrier);
}

/**
 * @brief Función usada de "start routine" al lanzar el hilo.
 *
 * @param args Puntero a una estructura de tipo `react_args_t` con el descriptor de
 * la conexión y la función de procesamiento de peticiones.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void *react_process(void *args) {
    p_process_func process;
    int connection_fd;

    sem_wait(mutex);
    process = ((react_args_t *)args)->process;
    connection_fd = ((react_args_t *)args)->connection_fd;

    pthread_cleanup_push(react_cleanup_fd, (void *)&connection_fd);
    pthread_cleanup_push(react_child_cleanup, NULL);
    sem_post(mutex);
    sem_post(s_accept);

    if (-1 == block_all_signals()) {
        pthread_exit(NULL);
    }

    process(connection_fd);

    pthread_cleanup_pop(1);
    pthread_cleanup_pop(1);
    return NULL;
}

int react_dispatch_thread(p_process_func process, int connection_fd) {
    pthread_t tid;
    int ret;

    sem_wait(s_accept); // Para evitar cambiar la estructura react_args_t mientras la usa otro hilo
    sem_wait(mutex);    // Controla el acceso a la tabla threads
    args.process = process;
    args.connection_fd = connection_fd;

    if (0 != (ret = pthread_create(&tid, NULL, react_process, (void *)&args))) {
        log_error(strerror(ret));
        close(connection_fd);
        sem_post(mutex);
        sem_post(barrier);
        return -1;
    }
    threads[n_threads] = tid;
    n_threads++;
    if (0 != (ret = pthread_detach(tid))) {
        log_error(strerror(ret));
        pthread_cancel(tid);
        pthread_join(tid, NULL);
        n_threads--;
        close(connection_fd);
        sem_post(mutex);
        sem_post(barrier);
        return -1;
    }

    sem_post(mutex);

    log_info("New thread dispatched.");
    return 0;
}