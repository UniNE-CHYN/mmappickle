from setuptools import setup
setup(
    name='mmappickle',
    description='This module enables to store large structures in a python pickle, in such a way that the data can be mmap\'ed instead of being copied in memory.', 
    version='1.0.0',
    packages=['mmappickle','mmappickle.stubs','mmappickle.picklers'],
    author="Laurent Fasnacht",
    author_email="l@libres.ch", 
    url = 'https://github.com/UniNE-CHYN/mmappickle'
)
