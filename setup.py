from setuptools import setup
import re

version_data = open("mmappickle/_version.py", "r").read()
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_data, re.M)

if mo:
    version_string = mo.group(1)
else:
    raise RuntimeError("Unable to find version string")


setup(
    name='mmappickle',
    description='This module enables to store large structures in a python pickle, in such a way that the data can be mmap\'ed instead of being copied in memory.', 
    version=version_string,
    packages=['mmappickle','mmappickle.stubs','mmappickle.picklers'],
    author="Laurent Fasnacht",
    author_email="l@libres.ch", 
    url = 'https://github.com/UniNE-CHYN/mmappickle'
)
