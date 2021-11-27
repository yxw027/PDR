import os
import re
from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


with open(os.path.join(os.path.dirname(__file__), 'pdr', '__init__.py')) as f:
    version = re.search("__version__ = '([^']+)'", f.read()).group(1)


with open('requirements.txt') as reqs_f:
    reqs = reqs_f.read().strip().split('\n')


setup(
    name='pdr',
    version=version,
    description='Pedestrian DeadReckoning',
    url='git@github.com:eternalamit5/PDR.git',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Amit Kumar Singh',
    author_email='sin@biba.uni-bremen.de',
    license='MIT License',
    packages=find_packages(),
    scripts=['bin/pdr'],
    install_requires=reqs,
    include_data_package=True,
    zip_safe=False
)
