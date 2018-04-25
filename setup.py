from setuptools import setup, find_packages
import re

version_data = open("mmappickle/_version.py", "r").read()
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_data, re.M)

if mo:
    version_string = mo.group(1)
else:
    raise RuntimeError("Unable to find version string")

long_description = open('README.md', 'r').read()

def test_suite():
    import unittest
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite

_setup_data = {
    #Base information
    'name': 'mmappickle',
    'version': version_string,
    'packages': find_packages(),
    'test_suite': 'setup.test_suite',
    'tests_require': ['numpy'],
    
    #Description and classification
    'description': 'Mmappickle is a Python 3 library which enables storing large numpy arrays into a file, along with the associated metadata, and to retrieve it in such a way that the numpy array are memory-mapped (numpy.memmap) instead of copied into the system memory.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'classifiers': [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research', 
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'        
    ],
    
    #Author and license...
    'author': "Laurent Fasnacht",
    'author_email': "l@libres.ch", 
    'maintainer': "Laurent Fasnacht",
    'maintainer_email': "l@libres.ch", 
    'url': 'https://github.com/UniNE-CHYN/mmappickle',
    'license': 'LGPLv3',

    #Requirements
    'python_requires': '>=3.4',
    #Numpy is required to have memmap array, but it still makes sense to use this module
    #without it, so it is not a requirement per-se.
    'install_requires': [],
}

if __name__ == '__main__':
    setup(**_setup_data)
