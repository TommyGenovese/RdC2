/**
 * @file config.c
 * @brief Fichero de implementación para el módulo config, que se encarga de la configuración
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 11-03-2025
 */

#include "config/config.h"

// Valores iniciales de la configuración
config_t config = {.config_dir = "",
                   .config_path = "",
                   .listen_port = PORT,
                   .max_clients = 1,
                   .server_mode = ITERATIVE,
                   .server_root = NULL,
                   .server_signature = NULL,
                   .logger_path = NULL};


/**
 * @brief Función que encuentra la ruta del directorio del ejecutable y la almacena,
 * así como la ruta del fichero de configuración.
 *
 * @param config El puntero a la estructura de configuración.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se obtiene la ruta con éxito, -1 en caso de error.
 */
static int config_obtain_path(config_t *config) {
    int i = 0;

    if (NULL == config) {
        return -1;
    }

    // Obtiene la ruta completa del ejecutable
    if (-1 == readlink("/proc/self/exe", config->config_dir, MAX_FULL_PATH)) {
        perror("readlink");
        return -1;
    }

    if (strlen(config->config_dir) >= MAX_FULL_PATH) {
        return -1;
    }

    // Quita el nombre del ejecutable para obtener la ruta del directorio
    for (i = strlen(config->config_dir) - 1; i >= 0; i--) {
        if (config->config_dir[i] == '/') {
            config->config_dir[++i] = '\0';
            break;
        }
    }
    if (i < 0) {
        config->config_dir[0] = '/';
        config->config_dir[1] = '\0';
    }

    // Se concatena server.conf para obtener la ruta del fichero
    strncpy(config->config_path, config->config_dir, i);
    strcat(config->config_path, "server.conf");

    return 0;
}

/**
 * @brief Quita los espacios de una cadena para obtener una única palabra que
 * se utilizará como clave o valor de uno de los pares de la configuración.
 *
 * Si la clave o el valor están formados por varias palabras separadas por espacios,
 * el uso de esta función implica que solo se utiliza la primera de las palabras.
 *
 * @param str La cadena a procesar.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return El puntero a la primera palabra encontrada en la cadena, o NULL
 * si no se encuentra la palabra.
 */
static char *remove_spaces(char *str) {
    int len, i;
    char word_found = 0;
    char *ret;

    len = strlen(str);
    ret = str;

    for (i = 0; i < len; i++) {
        if (str[i] == ' ') {  // Si el caracter actual es un espacio
            if (word_found) { // Si ya se había encontrado la palabra, ha terminado
                ret[i] = '\0';
                break;
            } else { // Si no, sigue avanzando
                ret++;
            }
        } else { // Si no es un espacio, se ha encontrado la palabra
            word_found = 1;
        }
    }
    if (!word_found) { // Si se recorre la cadena completa y no hay palabra, retornar NULL
        return NULL;
    }

    return ret;
}

/**
 * @brief Función que almacena un valor para una clave en la configuración.
 *
 * Si ya se había dado un valor para la clave, se descarta el valor antiguo y
 * se guarda el nuevo.
 *
 * Esta función no comprueba si los valores dados son válidos, esto es tarea de
 * las funciones que los utilicen.
 *
 * @param key Clave
 * @param value Valor
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se almacenan los datos con éxito o la clave no coincide con una de las
 * disponibles, -1 si hay algún error
 */
static int set_key_value(char *key, char *value) {
    char *aux = NULL, *aux2 = NULL;

    // Se obtiene la palabra sin espacios para la clave
    aux = remove_spaces(key);
    if (NULL == aux) {
        return 0;
    }

    // Se compara la clave con las disponibles
    if (0 == strncasecmp(key, "server_signature", strlen("server_signature"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }
        aux2 = calloc(strlen(aux) + 1, sizeof(char));
        if (NULL == aux2) {
            return -1;
        }
        if (NULL != config.server_signature) {
            free(config.server_signature);
        }

        config.server_signature = aux2;
        strcpy(config.server_signature, aux);

    } else if (0 == strncasecmp(key, "server_root", strlen("server_root"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }
        aux2 = calloc(strlen(config.config_dir) + strlen(aux) + 1, sizeof(char));
        if (NULL == aux2) {
            return -1;
        }
        if (NULL != config.server_root) {
            free(config.server_root);
        }
        
        config.server_root = aux2;
        // En el caso del directorio raíz, se almacena la ruta completa dada por
        // config.config_dir + el valor leído
        strcpy(config.server_root, config.config_dir);
        strcat(config.server_root, aux);

    } else if (0 == strncasecmp(key, "listen_port", strlen("listen_port"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }

        config.listen_port = atoi(aux);

    } else if (0 == strncasecmp(key, "max_clients", strlen("max_clients"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }

        config.max_clients = atoi(aux);

    } else if (0 == strncasecmp(key, "logger_path", strlen("logger_path"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }
        aux2 = calloc(strlen(config.config_dir) + strlen(aux) + 1, sizeof(char));
        if (NULL == aux2) {
            return -1;
        }
        if (NULL != config.logger_path) {
            free(config.logger_path);
        }

        config.logger_path = aux2;
        // En el caso del fichero de loggeo, se almacena la ruta completa dada por
        // config.config_dir + el valor leído
        strcpy(config.logger_path, config.config_dir);
        strcat(config.logger_path, aux);

    } else if (0 == strncasecmp(key, "server_mode", strlen("server_mode"))) {
        // Se obtiene la palabra sin espacios para el valor
        aux = remove_spaces(value);
        if (NULL == aux) {
            return -1;
        }
        if (0 == strncasecmp(aux, "pool", strlen("pool"))) {
            config.server_mode = POOL;
        } else if (0 == strncasecmp(aux, "reactive", strlen("reactive"))) {
            config.server_mode = REACTIVE;
        }
    }

    return 0;
}

void config_cleanup(void) {
    if (NULL != config.server_root) {
        free(config.server_root);
    }
    if (NULL != config.server_signature) {
        free(config.server_signature);
    }
    if (NULL != config.logger_path) {
        free(config.logger_path);
    }
}

int config_start() {
    FILE *f = NULL;
    char current[BUFF_SIZE];
    int new_line = 1, i = 0, eof = 0;
    char *key = NULL, *value = NULL;
    int status = -1;

    // Obtiene la ruta
    if (-1 == config_obtain_path(&config)) {
        return -1;
    }

    // Abre el fichero de configuración
    f = fopen(config.config_path, "r");
    if (NULL == f) {
        perror("fopen");
        return -1;
    }

    // registra la función de limpieza
    if (0 != atexit(config_cleanup)) {
        fprintf(stderr, "Unable to push cleanup function for configuration.\n");
        fclose(f);
        return -1;
    }

    // Bucle de lectura del fichero
    while (!eof) {
        if (new_line) { // Si se trata del comienzo de una línea
            // Se lee el primer caracter
            if (EOF == fscanf(f, "%c", current)) {
                eof = 1;
                break;
            }
            if ('\n' == *current) { // Si es un salto de línea, siguiente iteración
                continue;
            }
            if ('#' == *current) {         // Si es '#', la línea es un comentario
                while ('\n' != *current) { // Leer hasta cambiar de línea
                    if (EOF == fscanf(f, "%c", current)) {
                        eof = 1;
                        break;
                    }
                }
                continue;
            }
            // Si se trata de otro caracter, desactivamos la bandera de nueva línea
            new_line = 0;
        } else {
            i = 0; // Se lee hasta el cambio de línea o el fin de fichero
            while ((current[i] != '\n') && (++i < BUFF_SIZE)) {
                if (EOF == fscanf(f, "%c", current + i)) {
                    current[i] = '\n';
                    eof = 1;
                    break;
                }
            }
            if (current[i] != '\n') {
                continue;
            }
            new_line = 1;
            status = 0;
            // Separa la línea en clave y valor
            key = strtok(current, "=");
            value = strtok(NULL, "\n");
            // Guarda el par clave valor en la estructura
            status = set_key_value(key, value);
            if (status == -1) {
                fclose(f);
                return status;
            }
            status = 0;
            strcpy(current, "");
        }
    }

    fclose(f);

    // Se comprueba si los parámetros obligatorios se han completado
    if (NULL == config.server_root || NULL == config.server_signature || NULL == config.logger_path) {
        return -1;
    }

    return status;
}

void config_dump(char *filename) {
    FILE *fdump = NULL;
    int dir_end;

    dir_end = strlen(config.config_dir);
    fdump = fopen(filename, "w");
    fprintf(fdump, "server_root = %s\n", config.server_root + dir_end);
    fprintf(fdump, "server_signature = %s\n", config.server_signature);
    fprintf(fdump, "logger_path = %s\n", config.logger_path + dir_end);
    fprintf(fdump, "max_clients = %d\n", config.max_clients);
    fprintf(fdump, "listen_port = %d\n", config.listen_port);
    fprintf(fdump, "server_mode = %s\n", (config.server_mode == POOL ? "pool" : (config.server_mode == REACTIVE ? "reactive" : "iterative")));
    fclose(fdump);
}