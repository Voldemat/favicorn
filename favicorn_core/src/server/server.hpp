#ifndef INCLUDE_SERVER_H_
#define INCLUDE_SERVER_H_

#include <netinet/in.h>


class Server {
private:
    sockaddr_in addr;
    int server_id;
    char buffer[1500];
public:
    Server(const uint32_t host, const uint16_t port);
    int start();
    void receive() const;
    const char* get_buffer() const;
    ~Server();
};

#endif