#include "src/server/server.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>

#include "pybind11/detail/common.h"
#include "pybind11/pytypes.h"

PYBIND11_MODULE(favicorn_core, module) {
    namespace py = ::pybind11;
    pybind11::class_<Server>(module, "Server")
        .def(py::init<const py::object &, const uint16_t &>())
        .def("get_request", &Server::get_request)
        .def("exchange_events", &Server::exchange_events);
}
