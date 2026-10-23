# Coordinator regression tests

From the repository root, install PyModbus and run the standard-library suite:

```sh
python -m pip install pymodbus==3.13.1
python -m unittest discover -s tests -v
```

The tests use the actual integration coordinator and PyModbus client against a
read-only Modbus TCP peer on localhost. No sauna, credentials or external network
access are needed. The Home Assistant coordinator base and executor interface are
stubbed, so the suite does not require a complete Home Assistant installation.
These focused tests do not replace full Home Assistant lifecycle testing.

The suite checks normal reads, recovery after transport and Modbus failures,
failed connection cleanup, once-only register/coil write failures, serialization
of I/O and shutdown behavior. The local peer rejects real write requests.
