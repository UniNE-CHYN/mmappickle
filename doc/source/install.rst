.. _install:

Installation
============

``mmappickle`` can be installed either using ``pip``, or from source.

Since ``mmappickle`` requires ``Python 3``, you should ensure that you're using the correct ``pip`` executable. On some distributions, the executable is named ``pip3``.

It is possible to check the ``Python`` version of ``pip`` using:

.. code-block:: none

    pip -V
    
Similarly, you may need to use ``py.test-3`` instead of ``py.test``.

Installing using ``pip``
------------------------

To install using ``pip``, simply run:

.. code-block:: none

    pip install mmappickle

Manual installation from source
-------------------------------

To install manually, run the following:

.. code-block:: none

    git clone https://github.com/UniNE-CHYN/mmappickle
    cd mmappickle
    pip install .

To contribute, use ``pip install -e`` instead of ``pip install``. This sets a link to the source folder in the python installation, instead of copying the files.

It is advisable to run the tests to ensure that everything is working. This can be done by running the following command in the ``mmappickle`` directory:

.. code-block:: none

    py.test
