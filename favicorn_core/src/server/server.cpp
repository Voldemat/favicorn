#include "src/server/server.hpp"

#include <netinet/in.h>
#include <sys/_endian.h>
#include <sys/_types/_ssize_t.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <iostream>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <tuple>
#include <unordered_map>

#include "pybind11/cast.h"
#include "pybind11/pytypes.h"
#include "uuid.hpp"
#include "uv.h"
#include "uv/unix.h"

#include "src/http_parser/http_parser.hpp"
#include "src/loop/loop.hpp"

#define RAISE_ON_ERROR(error)                         \
    if (error != 0) {                                 \
        throw std::runtime_error(uv_strerror(error)); \
    };
struct write_handle : uv_write_t {
    bool more_body = true;
};
void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    buf->base = (char *)malloc(suggested_size);
    buf->len = suggested_size;
};

void on_close(uv_handle_t *handle) {
    std::cout << "On close: " << (void*) handle << std::endl;
    free(handle);
}

void server_write(uv_write_t *req, int status) {
    if (status == -1) {
        std::cerr << "Write error!\n" << std::endl;
    }
    if (!((write_handle *)req)->more_body) {
        uv_close((uv_handle_t *)req->handle, on_close);
    };
    char *base = (char *)req->data;
    free(base);
    free(req);
}
void on_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
    if (nread > 0) {
        const auto buffer = uv_buf_init(buf->base, nread);
        const auto &server = (Server *)client->loop->data;
        const auto &[request, error] =
            server->parser.parse_request(buf->base, nread);
        if (error != nullptr) {
            std::cerr << error << std::endl;
            delete error;
        } else {
            server->add_request(request, client);
            uv_read_stop(client);
        };
    }
    if (nread < 0) {
        std::cerr << "Read error: " << uv_strerror(nread) << std::endl;
        std::cout << "read before uv_close" << std::endl;
        uv_close((uv_handle_t *)client, on_close);
    }

    if (buf->base != nullptr) {
        free(buf->base);
    };
}

void loop_visitor(uv_check_t *handle) {
    const auto server = (Server *)handle->data;
    while (server->transport_queue.size() != 0) {
        const auto [request_id, length, buffer, more_body] =
            server->transport_queue.front();
        const auto client = server->request_id_to_client[request_id];
        const auto new_request_id = request_id;
        if (length == -1) {
            if (!uv_is_closing((uv_handle_t *)client)) {
                std::cout << "Closing client: " << (void *)client;
                uv_close((uv_handle_t *)client, on_close);
            };
            delete server->request_id_to_client[request_id];
        } else {
            write_handle *req = (write_handle *)malloc(sizeof(write_handle));
            uv_buf_t wrbuf = uv_buf_init((char *)buffer, length);
            req->more_body = more_body;
            std::cout << (void *)client << " uv_write: " << client->type
                      << ", request_id: " << request_id << std::endl;
            uv_write(req, (uv_stream_t *)client, &wrbuf, 1, server_write);
        }
        server->transport_queue.pop_front();
        const auto t = std::make_tuple(new_request_id, std::nullopt);
        server->controller_queue.push_back(t);
    }
};

void on_new_connection(uv_stream_t *server, int status) {
    if (status != 0) {
        std::cerr << uv_strerror(status) << std::endl;
        return;
    };
    uv_tcp_t *client = (uv_tcp_t *)malloc(sizeof(uv_tcp_t));
    uv_tcp_init(server->loop, client);
    if (uv_accept(server, (uv_stream_t *)client) == 0) {
        std::cout << "Accept client: " << (void *)client
                  << ", type: " << client->type << std::endl;
        uv_read_start((uv_stream_t *)client, alloc_buffer, on_read);
    } else {
        uv_close((uv_handle_t *)client, on_close);
    }
}

Server::Server(const pybind11::object &host, const uint16_t &port)
    : buffer{""}, parser{} {
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(host.attr("__int__")().cast<int>());
    addr.sin_port = htons(port);
    loop.data = this;
    t = std::thread(&Server::thread_main, this);
};

void Server::thread_main() {
    std::cout << "Successfully initialized the loop" << std::endl;
    uv_tcp_t server;
    int error = uv_tcp_init(&loop, &server);
    RAISE_ON_ERROR(error)
    std::cout << "Successfully initialized tcp server" << std::endl;
    error = uv_tcp_bind(&server, (const struct sockaddr *)&addr, 0);
    RAISE_ON_ERROR(error)
    std::cout << "Binded tcp server" << std::endl;
    error = uv_listen((uv_stream_t *)&server, 5, on_new_connection);
    RAISE_ON_ERROR(error)
    std::cout << "Tcp server started listening" << std::endl;
    uv_check_t check_handler;
    uv_check_init(&loop, &check_handler);
    check_handler.data = this;
    uv_check_start(&check_handler, (uv_check_cb)loop_visitor);
    loop.run_forever();
    const auto exc = loop.close();
    if (exc.has_value()) {
        std::cout << "Error closing event loop: " << exc->what() << std::endl;
    }
};

const pybind11::object Server::get_request() {
    if (requests_queue.size() == 0) return pybind11::none();
    const auto &[request_id, request] = requests_queue.front();
    const auto scope = request_to_asgi_scope(request);
    const auto tuple = pybind11::make_tuple(request_id, scope);
    delete request;
    requests_queue.pop_front();
    return tuple;
};

const pybind11::dict Server::request_to_asgi_scope(
    const HTTPRequest *const request) {
    const auto headers = pybind11::tuple(request->headers.size());
    int index = 0;
    for (const auto &[key, value] : request->headers) {
        headers[index] = pybind11::make_tuple(key, value);
        index++;
    };
    const auto dict = pybind11::dict();
    dict["type"] = "http";
    dict["version"] = "3.0";
    dict["http_version"] = request->http_version;
    dict["method"] = request->method;
    dict["path"] = request->url.get();
    dict["headers"] = headers;
    return dict;
};

void Server::add_request(const HTTPRequest *request,
                         const uv_stream_t *client) {
    const auto request_id = std::to_string(std::hash<void*>{}((void*)client));
    std::cout << "Add request: request_id: " << request_id
              << ", client: " << (void *)client << std::endl;
    request_id_to_client[request_id] = client;
    requests_queue.push_back(std::make_tuple(request_id, request));
};

const pybind11::object Server::exchange_events(const pybind11::list events) {
    for (const auto &el : events) {
        const pybind11::tuple tuple = el.cast<pybind11::tuple>();
        const std::string request_id = tuple[0].cast<std::string>();
        const std::string event_type = tuple[1]["type"].cast<std::string>();
        if (event_type == "http.response.start") {
            const int status = tuple[1]["status"].cast<int>();
            std::ostringstream oss;
            oss << "HTTP/1.1 " << std::to_string(status) << " OK\r\n";
            const auto py_headers = tuple[1]["headers"].cast<pybind11::list>();
            for (int i = 0; i < py_headers.size(); i++) {
                const pybind11::tuple py_tuple = py_headers[i];
                std::string header_key = py_tuple[0].cast<std::string>();
                std::string header_value = py_tuple[1].cast<std::string>();
                oss << header_key << ": " << header_value << "\r\n";
            }
            oss << "\r\n";
            char *buf = (char *)malloc(oss.str().size());
            memcpy(buf, oss.str().c_str(), oss.str().size());
            transport_queue.push_back(
                std::make_tuple(request_id, oss.str().size(), buf, true));
        } else if (event_type == "http.response.body") {
            const bool more_body = tuple[1]["more_body"].cast<bool>();
            const std::string body = tuple[1]["body"].cast<std::string>();
            char *buf = (char *)malloc(body.size());
            memcpy(buf, body.c_str(), body.size());
            transport_queue.push_back(
                std::make_tuple(request_id, body.size(), buf, more_body));
        }
    }
    pybind11::list new_events = pybind11::list();
    while (controller_queue.size() != 0) {
        const auto &[request_id, data] = controller_queue.front();
        new_events.append(pybind11::make_tuple(request_id, data));
        controller_queue.pop_front();
    };
    return new_events;
}

Server::~Server() {
    std::cout << "Destructor" << std::endl;
    loop.stop();
    t.join();
};
