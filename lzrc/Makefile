CFLAGS ?= -O2 -fPIC -w

all: libps3lzrc.so

libps3lzrc.so: ps3lzrc.c
	$(CC) $(CFLAGS) -shared -o $@ $<

clean:
	rm -f libps3lzrc.so

# Windows (MinGW): gcc -O2 -w -shared -static-libgcc -o ps3lzrc.dll ps3lzrc.c
