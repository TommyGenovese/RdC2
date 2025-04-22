#ifndef _SERVER_H
#define _SERVER_H

#include "server/start.h"
#include "server/utils.h"
#include "server/reactive.h"
#include "server/pool.h"

typedef enum _server_mode_t {
    ITERATIVE,
    REACTIVE,
    POOL
} server_mode_t;

#endif