#include <Python.h>

static PyObject* dummy_placeholder(PyObject* self, PyObject* args) {
    Py_RETURN_NONE;
}

static PyMethodDef DummyMethods[] = {
    {"placeholder", dummy_placeholder, METH_VARARGS, "A dummy placeholder"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef dummy_module = {
    PyModuleDef_HEAD_INIT,
    "dummy",      // module name (must match last component of pxr.dummy)
    NULL,         // doc
    -1,           // size
    DummyMethods
};

PyMODINIT_FUNC PyInit_dummy(void) {
    return PyModule_Create(&dummy_module);
}
