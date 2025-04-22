/**
 * @file logger.c
 * @brief Fichero de implementación para el módulo logger, que se encarga del fichero de loggeo
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 11-03-2025
 */

#include "logger/logger.h"

sem_t file_sem;  // Mutex para el fichero, evita que los hilos dejen mensajes intercalados.
int log_fd = -1; // Descriptor de fichero de loggeo.

int logger_write(const char *mode, const char *msg) {
    char *string_out;
    int length, byte_count, write_ret;
    time_t raw_time;
    struct tm *log_time;
    char *time_str;

    // Obtención de fecha y hora
    time(&raw_time);
    log_time = localtime(&raw_time);
    time_str = asctime(log_time);
    time_str = strtok(time_str, "\n");

    // Construscción de la cadena a escribir completa
    length = strlen(time_str) + strlen(mode) + strlen(msg) + 6;
    string_out = calloc(length + 1, sizeof(char));
    if (NULL == string_out) {
        return -1;
    }
    sprintf(string_out, "[%s] %s: %s\n", time_str, mode, msg);

    // Escritura, protegida por semáforo
    sem_wait(&file_sem);
    byte_count = 0;
    while (length > byte_count) {
        write_ret = write(log_fd, string_out + byte_count, length - byte_count);
        if (write_ret <= 0) {
            sem_post(&file_sem);
            free(string_out);
            return -1;
        }
        byte_count += write_ret;
    }
    sem_post(&file_sem);

    free(string_out);
    return 0;
}

int logger_start(const char *logfile_name) {

    // Apertura del fichero, si ya existe añade al final y si no lo crea
    log_fd = open(logfile_name, O_RDWR | O_CREAT | O_APPEND, S_IWUSR | S_IWGRP | S_IWOTH | S_IRUSR | S_IRGRP | S_IROTH);
    if (-1 == log_fd) {
        perror("open");
        return -1;
    }

    // Inicializa el semáforo del fichero
    if (-1 == sem_init(&file_sem, 0, 1)) {
        log_warning("Unable to create lock for logger file. Logs might be interleaved.");
    }

    // Registra la función de limpieza con atexit
    if (0 != atexit(logger_end)) {
        log_warning("Unable to push cleanup function for logger. Logger cleanup must be managed manually.");
    }

    printf("Logging output to file: %s\n", logfile_name);
    return 0;
}

int log_error(const char *msg) {
    return logger_write(ERROR, msg);
}

int log_info(const char *msg) {
    return logger_write(INFO, msg);
}

int log_warning(const char *msg) {
    return logger_write(WARNING, msg);
}

void logger_end(void) {
    close(log_fd);
    sem_destroy(&file_sem);
}
