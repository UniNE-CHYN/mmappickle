Contributing guide
==================

``mmappickle`` is a free software, and all contributions are welcome, whether they are bug reports, source code, or documentation.

.. _reporting-bugs:

Reporting bugs
--------------

To report bugs, open an issue in the `issue tracker <https://github.com/UniNE-CHYN/mmappickle/issues>`_.

Ideally, a bug report should contain at least the following information:

- a minimum code example to trigger the bug
- the expected result
- the result obtained.


Quick guide to contributing code or documentation
-------------------------------------------------

To contribute, you'll need `Sphinx <http://www.sphinx-doc.org>`_ to build the documentation, and `pytest <http://pytest.org>`_ to run the tests.

If for some reason you are not able to run the following steps, simply open an issue with your proposed change.

1. `Fork <https://help.github.com/articles/fork-a-repo/>`_ the `mmappickle <https://github.com/UniNE-CHYN/mmappickle>`_ on GitHub. 
2. Clone your fork to your local machine:

.. code-block:: none

    git clone https://github.com/<your username>/mmappickle.git
    cd mmappickle
    pip install -e .

3. Create a branch for your changes:

.. code-block:: none

    git checkout -b <branch-name>
    
4. Make your changes. 
5. If you're writing code, you should write some tests, ensure that all the tests pass and that the code coverage is good. This can be done using:

.. code-block:: none

    py.test --cov=mmappickle --pep8
  
6. You should also check that the documentation compiles and that the result look good. The documentation can be seen by opening a browser in `doc/html`. You can (re)build it using the following command line (make sure that there is no warnings):

.. code-block:: none

    sphinx-build doc/source doc/html
  

7. Commit your changes and push to your fork on GitHub:

.. code-block:: none

    git add .
    git commit -m "<description-of-changes>"
    git push origin <name-for-changes>

8. Submit a `pull request <https://help.github.com/articles/creating-a-pull-request/>`_.

