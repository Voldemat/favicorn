#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "server.hpp"


static PyMethodDef ExtensionMethods[] = {
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef core_module = {
    PyModuleDef_HEAD_INIT,
    "favicorn_core",
    NULL,
    -1,
    NULL
};


PyMODINIT_FUNC PyInit_favicorn_core() {
    PyObject* module = PyModule_Create(&core_module);

    PyObject *myclass = PyType_FromSpec(&server_spec);
    if (myclass == NULL){
        return NULL;
    };
    Py_INCREF(myclass);

    if(PyModule_AddObject(module, "Server", myclass) < 0){
        Py_DECREF(myclass);
        Py_DECREF(module);
        return NULL;
    };
    return module;
};
