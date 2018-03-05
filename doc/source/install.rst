.. _install:

Installation
============

``mmappickle`` can be installed either using ``pip``, or from source.

Installing using ``pip``
------------------------

To install using ``pip``, simply run:

.. code-block:: none

    pip3 install mmappickle

Manual installation from source
-------------------------------

To install manually, run the following:

.. code-block:: none

    git clone https://github.com/UniNE-CHYN/mmappickle
    cd mmappickle
    sudo python3 setup.py install
    
If root access is not available, simply add ``--user`` to the last command line.

To contribute, use ``develop`` instead of ``install``. This sets a link to the source folder in the python installation, instead of copying the files.
