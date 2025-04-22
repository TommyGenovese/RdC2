DOBJ= obj/
DLIB= lib/
DSRC= src/
DSRCL= srclib/
DBIN= bin/
SERVER= web_server
# Añadir ejecutables
EXE= $(DBIN)$(SERVER)

DSERVERSRC= $(DSRCL)server/
DSERVEROBJ= $(DOBJ)server/
DLOGGERSRC= $(DSRCL)logger/
DLOGGEROBJ= $(DOBJ)logger/
DHTTPSRC= $(DSRCL)http/
DHTTPOBJ= $(DOBJ)http/
DCONFIGSRC= $(DSRCL)config/
DCONFIGOBJ= $(DOBJ)config/

CC= @gcc
CFLAGS= -c -Wall -Wextra -g
IFLAGS= -Iincludes/
LFLAGS= -L$(DLIB) -lserver -llogger -lhttp

all: dirs $(DLIB)libserver.a $(DLIB)liblogger.a $(DLIB)libconfig.a $(DLIB)libhttp.a $(EXE)

# Si no existen los directorios de objetos y librerías, los crea
dirs:
	@mkdir -p $(DOBJ)
	@mkdir -p $(DSERVEROBJ)
	@mkdir -p $(DHTTPOBJ)
	@mkdir -p $(DLOGGEROBJ)
	@mkdir -p $(DCONFIGOBJ)
	@mkdir -p $(DLIB)
	@mkdir -p $(DBIN)

$(DOBJ)%.o: $(DSRC)%.c
	$(CC) $(CFLAGS) $(IFLAGS) $(LFLAGS) $< -o $@
	@printf "[\033[1;32mCompiled\033[0m] $<\n"

$(DLIB)libserver.a: $(DSERVERSRC)utils.c $(DSERVERSRC)start.c $(DSERVERSRC)reactive.c $(DSERVERSRC)pool.c
	$(CC) $(CFLAGS) $(IFLAGS) $(DSERVERSRC)utils.c -o $(DSERVEROBJ)utils.o
	$(CC) $(CFLAGS) $(IFLAGS) $(DSERVERSRC)start.c -o $(DSERVEROBJ)start.o
	$(CC) $(CFLAGS) $(IFLAGS) $(DSERVERSRC)reactive.c -o $(DSERVEROBJ)reactive.o
	$(CC) $(CFLAGS) $(IFLAGS) $(DSERVERSRC)pool.c -o $(DSERVEROBJ)pool.o
	@ar rcs $@ $(DSERVEROBJ)utils.o $(DSERVEROBJ)start.o $(DSERVEROBJ)reactive.o $(DSERVEROBJ)pool.o
	@printf "[\033[1;34mBuilt\033[0m] $@\n"

$(DLIB)liblogger.a: $(DLOGGERSRC)logger.c
	$(CC) $(CFLAGS) $(IFLAGS) $(DLOGGERSRC)logger.c -o $(DLOGGEROBJ)logger.o
	@ar rcs $@ $(DLOGGEROBJ)logger.o
	@printf "[\033[1;34mBuilt\033[0m] $@\n"

$(DLIB)libhttp.a: $(DHTTPSRC)http_response.c $(DHTTPSRC)cgi.c
	$(CC) $(CFLAGS) $(IFLAGS) $(DHTTPSRC)http_response.c -o $(DHTTPOBJ)http_response.o
	$(CC) $(CFLAGS) $(IFLAGS) $(DHTTPSRC)cgi.c -o $(DHTTPOBJ)cgi.o
	@ar rcs $@ $(DHTTPOBJ)http_response.o $(DHTTPOBJ)cgi.o
	@printf "[\033[1;34mBuilt\033[0m] $@\n"

$(DLIB)libconfig.a: $(DCONFIGSRC)config.c
	$(CC) $(CFLAGS) $(IFLAGS) $(DCONFIGSRC)config.c -o $(DCONFIGOBJ)config.o
	@ar rcs $@ $(DCONFIGOBJ)config.o
	@printf "[\033[1;34mBuilt\033[0m] $@\n"

$(DBIN)$(SERVER): $(DOBJ)$(SERVER).o $(DLIB)libserver.a $(DLIB)liblogger.a $(DLIB)libconfig.a $(DLIB)libhttp.a
	$(CC) $^ -o $@
	@printf "[\033[1;36mLinked\033[0m] $@\n"

clean:
	@rm -rf $(DOBJ)* $(DLIB)* $(EXE)
	@printf "[\033[1;31mRemoved\033[0m] $(DOBJ)* $(DLIB)* $(EXE)\n"

run: all
	@printf "[\033[1;33mLaunching\033[0m] $(EXE)\n"
	@printf "To close it, execute \033[1mpgrep $(SERVER) | xargs kill -SIGINT\033[0m in another terminal\n\n"
	@setsid -w ./$(EXE)
	@printf "\n[\033[1;33mTerminated\033[0m] Status code: $$?\n"