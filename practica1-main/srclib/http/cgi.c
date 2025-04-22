/**
 * @file cgi.c
 * @brief Fichero de implementación para el módulo http/cgi, que se encarga de la ejecución de scripts.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 15-03-2025
 */

#include "http/cgi.h"

/**
 * @struct args_t
 * @brief Estructura de datos que se utiliza para parseo de argumentos de scripts.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
typedef struct {
    char **args;  // Array de argumentos finalizado en NULL
    int n_args;   // Número de argumentos (incluyendo el puntero NULL)
    int max_args; // Máxima capacidad del array (incluyendo el puntero NULL)
} args_t;

char *stradd(char *orig, const char *src) {
    char *ret = NULL;

    if (NULL == orig) {
        ret = strdup(src);
        if (NULL == ret) {
            log_error(strerror(errno));
        }
    } else {
        ret = calloc(strlen(orig) + strlen(src) + 1, sizeof(char));
        if (NULL == ret) {
            log_error(strerror(errno));
            return orig;
        }
        strcpy(ret, orig);
        strcat(ret, src);
        free(orig);
    }

    return ret;
}

char unescape(char hi, char lo) {
    if (hi >= 'A') {
        hi = hi - 'A' + 10;
    } else {
        hi -= '0';
    }
    if (lo >= 'A') {
        lo = lo - 'A' + 10;
    } else {
        lo -= '0';
    }
    return (hi << 4) + (lo & 0x0F);
}


/**
 * @brief Añade un argumento a una estructura de tipo `args_t`.
 *
 * La función se encarga de crear una copia dinámica del argumento, `new`, y
 * añadirlo a la lista de argumentos de la estructura. Además, amplía el tamaño
 * de la lista de argumentos si es necesario, modifica el número y el máximo de
 * argumentos y añade el puntero `NULL` al final de la lista.
 *
 * Si la lista no está inicializada (no se ha reservado memoria), la incializa
 * con una llamada a `malloc`.
 *
 * La lista de la estructura deberá liberarse con `args_free` al acabar de usarla.
 *
 * @param orig La estructura con la lista de argumentos.
 * @param new La cadena con el argumento a añadir.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se añade el argumento correctamente, -1 si hay algún error (no se modifica la lista
 * si hay error).
 */
static int args_add(args_t *orig, const char *new) {
    char *new_arg = NULL;
    char **new_arg_list = NULL;
    size_t i, new_len;

    if (NULL == orig) {
        return -1;
    }
    if (NULL == (new_arg = strdup(new))) {
        return -1;
    }

    for (i = 0; i < strlen(new_arg); i++) {
        if (new_arg[i] == '+') {
            new_arg[i] = ' ';
        } else if (new_arg[i] == '%') {
            new_len = strlen(new_arg) - 2;
            if (i < new_len) {
                new_arg[i] = unescape(new_arg[i + 1], new_arg[i + 2]);
            }
            if (i + 1 < new_len) {
                memmove(new_arg + i + 1, new_arg + i + 3, new_len - i - 1);
            }
            new_arg[new_len] = '\0';
        }
    }

    if (NULL == orig->args) {
        orig->args = malloc(5 * sizeof(char *));
        if (NULL == orig->args) {
            free(new_arg);
            return -1;
        }
        orig->args[0] = new_arg;
        orig->args[1] = NULL;
        orig->max_args = 3;
        orig->n_args = 2;
    } else {
        if (orig->n_args == orig->max_args) {
            new_arg_list = realloc(orig->args, (orig->max_args + 5) * sizeof(char *));
            if (NULL == new_arg_list) {
                free(new_arg);
                return -1;
            }
            orig->args = new_arg_list;
            orig->max_args += 5;
        }

        orig->args[orig->n_args - 1] = new_arg;
        orig->args[orig->n_args++] = NULL;
    }

    return 0;
}

void args_free(void *args) {
    char **aux = (char **)args;
    int i = 0;

    if (NULL != aux) {
        while (NULL != aux[i]) {
            free(aux[i]);
            i++;
        }
        free(aux);
    }
}

char **parse_script_args(char *path) {
    char *aux = NULL;
    args_t args = {.args = NULL, .max_args = 0, .n_args = 0};

    aux = strtok(path, "?");
    if (NULL != strstr(path, ".php")) {
        args_add(&args, "/bin/php");
        args_add(&args, aux);
    } else if (NULL != strstr(path, ".py")) {
        args_add(&args, "/bin/python3");
        args_add(&args, "-u"); // Avoid buffering
        args_add(&args, aux);
    } else {
        return NULL;
    }

    while (1) {
        aux = strtok(NULL, "=");
        if (NULL == aux) {
            break;
        }
        aux = strtok(NULL, "&\0");
        if (-1 == args_add(&args, aux)) {
            break;
        }
    }

    return args.args;
}

char *cgi_get_script(char *const *argv, int connection_fd) {
    int parent_to_child[2], child_to_parent[2];
    pid_t pid;

    if (-1 == pipe(parent_to_child)) {
        log_error(strerror(errno));
        return NULL;
    }

    if (-1 == pipe(child_to_parent)) {
        log_error(strerror(errno));
        close(parent_to_child[READ_END]);
        close(parent_to_child[WRITE_END]);
        return NULL;
    }

    pid = fork();

    if (-1 == pid) {
        log_error(strerror(errno));
        close(parent_to_child[READ_END]);
        close(parent_to_child[WRITE_END]);
        close(child_to_parent[READ_END]);
        close(child_to_parent[WRITE_END]);
        return NULL;
    }

    if (pid == 0) { // Hijo
        close(parent_to_child[WRITE_END]);
        close(child_to_parent[READ_END]);
        dup2(parent_to_child[READ_END], STDIN_FILENO);
        close(parent_to_child[READ_END]);
        dup2(child_to_parent[WRITE_END], STDOUT_FILENO);
        close(child_to_parent[WRITE_END]);

        n_threads = 0;
        free(threads);
        sem_close(mutex);
        sem_close(barrier);
        sem_close(s_accept);
        close(connection_fd);
        cleanup_socket_fd();
        logger_end();
        config_cleanup();

        execv(argv[0], argv);
        log_error("Failed to launch CGI process.");
        exit(EXIT_FAILURE);
    } else {
        char buffer[BUFF_SIZE] = "";
        char *ret = NULL;
        int bytes_read = 0;
        close(parent_to_child[WRITE_END]);
        close(parent_to_child[READ_END]);
        close(child_to_parent[WRITE_END]);

        while (1) {
            bytes_read = read(child_to_parent[READ_END], buffer, BUFF_SIZE - 1);
            if (0 == bytes_read) {
                break;
            }
            if (bytes_read < 0) {
                log_error(strerror(errno));
            }
            buffer[bytes_read] = '\0';
            ret = stradd(ret, buffer);
        }

        close(child_to_parent[READ_END]);
        wait(NULL);
        return ret;
    }
}

char *cgi_post_script(char *const *argv, int connection_fd) {
    int parent_to_child[2], child_to_parent[2];
    pid_t pid;

    if (-1 == pipe(parent_to_child)) {
        log_error(strerror(errno));
        return NULL;
    }

    if (-1 == pipe(child_to_parent)) {
        log_error(strerror(errno));
        close(parent_to_child[READ_END]);
        close(parent_to_child[WRITE_END]);
        return NULL;
    }

    pid = fork();

    if (-1 == pid) {
        log_error(strerror(errno));
        close(parent_to_child[READ_END]);
        close(parent_to_child[WRITE_END]);
        close(child_to_parent[READ_END]);
        close(child_to_parent[WRITE_END]);
        return NULL;
    }

    if (pid == 0) { // Hijo
        close(parent_to_child[WRITE_END]);
        close(child_to_parent[READ_END]);
        dup2(parent_to_child[READ_END], STDIN_FILENO);
        close(parent_to_child[READ_END]);
        dup2(child_to_parent[WRITE_END], STDOUT_FILENO);
        close(child_to_parent[WRITE_END]);

        n_threads = 0;
        free(threads);
        sem_close(mutex);
        sem_close(barrier);
        sem_close(s_accept);
        close(connection_fd);
        cleanup_socket_fd();
        logger_end();
        config_cleanup();

        execv(argv[0], argv);
        log_error("Failed to launch CGI process.");
        exit(EXIT_FAILURE);
    } else {
        char buffer[BUFF_SIZE] = "";
        char arg = 0;
        char *ret = NULL;
        int bytes_read = 0, write_ret;
        close(parent_to_child[READ_END]);
        close(child_to_parent[WRITE_END]);

        struct timeval timeout = {.tv_sec = 3, .tv_usec = 0};
        setsockopt(connection_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

        while (1) {
            while (arg != '=') {
                bytes_read = read(connection_fd, &arg, 1);
                if (0 == bytes_read) {
                    break;
                }
                if (bytes_read < 0) {
                    if (EAGAIN != errno && EWOULDBLOCK != errno) {
                        log_error(strerror(errno));
                    }
                    break;
                }
            }
            if (bytes_read <= 0) {
                break;
            }
            while (1) {
                bytes_read = read(connection_fd, &arg, 1);
                if (0 == bytes_read) {
                    break;
                }
                if (bytes_read < 0) {
                    if (EAGAIN != errno && EWOULDBLOCK != errno) {
                        log_error(strerror(errno));
                    }
                    break;
                }
                if (arg == '&') {
                    break;
                }
                if (arg == '+') {
                    arg = ' ';
                }
                if (arg == '%') {
                    char hi, lo;
                    bytes_read = read(connection_fd, &hi, 1);
                    if (0 == bytes_read) {
                        break;
                    }
                    if (bytes_read < 0) {
                        if (EAGAIN != errno && EWOULDBLOCK != errno) {
                            log_error(strerror(errno));
                        }
                        break;
                    }
                    bytes_read = read(connection_fd, &lo, 1);
                    if (0 == bytes_read) {
                        break;
                    }
                    if (bytes_read < 0) {
                        if (EAGAIN != errno && EWOULDBLOCK != errno) {
                            log_error(strerror(errno));
                        }
                        break;
                    }
                    arg = unescape(hi, lo);
                }
                write_ret = write(parent_to_child[WRITE_END], &arg, 1);
                if (write_ret <= 0) {
                    if (EPIPE == errno) {
                        log_warning("Client closed the connection before receiving a response.");
                    } else {
                        log_error(strerror(errno));
                    }
                    break;
                }
            }
            if (bytes_read <= 0 || write_ret <= 0) {
                break;
            }
        }
        close(parent_to_child[WRITE_END]);

        while (1) {
            bytes_read = read(child_to_parent[READ_END], buffer, BUFF_SIZE - 1);
            if (0 == bytes_read) {
                break;
            }
            if (bytes_read < 0) {
                log_error("Error reading script output.");
                break;
            }
            buffer[bytes_read] = '\0';
            ret = stradd(ret, buffer);
        }

        timeout.tv_sec = 30;
        setsockopt(connection_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

        close(child_to_parent[READ_END]);
        wait(NULL);
        return ret;
    }
}
