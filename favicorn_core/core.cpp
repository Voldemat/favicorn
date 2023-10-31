#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "src/pyserver/pyserver.hpp"
#include "src/pyasgi/pyasgi.hpp"
#include "src/scope.hpp"
#include "src/module.hpp"


PyMODINIT_FUNC PyInit_favicorn_core() {
    PyObject* module = PyModule_Create(&extension::core_module);

    PyObject *server_class = PyType_FromSpec(&server_spec);
    if (server_class == NULL){
        return NULL;
    };
    Py_INCREF(server_class);

    if(PyModule_AddObject(module, "Server", server_class) < 0){
        Py_DECREF(server_class);
        Py_DECREF(module);
        return NULL;
    };
    PyObject *asgi_class = PyType_FromSpec(&pyasgi_spec);
    if (asgi_class == NULL){
        return NULL;
    };
    Py_INCREF(asgi_class);

    if(PyModule_AddObject(module, "ASGIManager", asgi_class) < 0){
        Py_DECREF(asgi_class);
        Py_DECREF(module);
        return NULL;
    };
    PyModule_AddStringConstant(module, SCOPE_TYPE, "type");
    return module;
};
