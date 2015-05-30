=============
Documentation
=============

-----
Build
-----

To build the documentation locally, follow these instructions:

1. Go to the root directory of this project.
2. Install the requirements::

     $ pip install -r docs/requirements.txt

   This will install sphinx, some required packages and the project in development mode (``pip install -e .``). That's why you have to be in the root dir.
3. Go to the docs dir::

     $ cd docs

4. Invoke sphinx build::

     $ sphinx-build -b html -d _build/doctrees   source _build/html

   or alternativly with make::

     $ make html

   on windows::

     $ make.bat html
