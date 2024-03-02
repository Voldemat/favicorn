#ifndef INCLUDE_SERVER_H_
#define INCLUDE_SERVER_H_

#include <Python.h>
#include <netinet/in.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#include <thread>
#include <tuple>
#include <unordered_map>

#include "pybind11/pytypes.h"
#include "uv.h"

#include "src/http_parser/http_parser.hpp"
#include "src/loop/loop.hpp"

class Server {
private:
    const char buffer[1500];
    std::thread t;
    void thread_main();
    std::deque<std::tuple<std::string, const HTTPRequest* const>> requests_queue;
    sockaddr_in addr;
    UVLoop loop;
    const pybind11::dict request_to_asgi_scope(
        const HTTPRequest* const request);

public:
    std::unordered_map<std::string, const uv_stream_t*>
        request_id_to_client;
    HTTPParser parser;
    std::deque<std::tuple<std::string, int, const char*, bool>> transport_queue;
    std::deque<std::tuple<std::string, std::optional<std::string>>> controller_queue;
    Server(const pybind11::object& host, const uint16_t& port);
    void add_request(const HTTPRequest* request, const uv_stream_t* client);
    const pybind11::object get_request();
    const pybind11::object exchange_events(const pybind11::list events);
    ~Server();
};

#endif
