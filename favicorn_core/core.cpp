#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>

#include "src/server/server.hpp"

// Create the Python module
PYBIND11_MODULE(favicorn_core, module)
{
    namespace py = ::pybind11;
    pybind11::class_<Server>(module, "Server")
        .def(py::init<const uint32_t &, const uint16_t&>())
        .def("start", &Server::start)
        .def("receive", &Server::receive);
}
