#ifndef INCLUDE_PYSERVER_H_
#define INCLUDE_PYSERVER_H_

#include <Python.h>
#include <structmember.h>
#include <new>

#include "src/server/server.hpp"


typedef struct {
    PyObject_HEAD
    Server*    m_myclass;
} PyServer;

int PyServer_init(PyObject* self, PyObject* args, PyObject* kwds);
PyObject* PyServer_new(PyTypeObject* subtype, PyObject *args, PyObject *kwds);
void PyServer_dealloc(PyServer* self);
PyObject* PyServer_start(PyObject *self, PyObject *args);
PyObject* PyServer_receive(PyObject *self, PyObject *args);

static PyMethodDef PyServer_methods[] = {
    {
        "start",
        (PyCFunction)PyServer_start,
        METH_NOARGS,
        PyDoc_STR("Create socket and bind to specified address")
    },
    {
        "receive",
        (PyCFunction)PyServer_receive,
        METH_NOARGS,
        NULL
    },
    {NULL, NULL} /* Sentinel */
};

static struct PyMemberDef PyServer_members[] = {
    {NULL} /* Sentinel */
};

static PyType_Slot PyServer_slots[] = {
    {Py_tp_new, (void*)PyServer_new},
    {Py_tp_init, (void*)PyServer_init},
    {Py_tp_dealloc, (void*)PyServer_dealloc},
    {Py_tp_members,  PyServer_members},
    {Py_tp_methods, PyServer_methods},
    {0, 0}
};

static PyType_Spec server_spec = {
    "Server",                                  // name
    sizeof(PyServer) + sizeof(Server),    // basicsize
    0,                                          // itemsize
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   // flags
    PyServer_slots                               // slots
};

#endif
