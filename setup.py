import sys
import os
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

HERE = os.path.dirname(os.path.abspath(__file__))
crace_path = os.path.join(HERE, "crace")
sys.path.insert(0, crace_path)

from crace_plot.settings.config import (
    package_name,
    version,
    author,
    author_email,
    description,
    url,
)

class CustomSDist(_sdist):
    """Custom sdist command to generate .zip source distribution."""
    def initialize_options(self):
        _sdist.initialize_options(self)
        self.formats = 'zip,tar,gztar'

setup(
    name=package_name,
    version=version,
    description=description,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author=author,
    author_email=author_email,
    url=url,

    packages=find_packages(where='.'),
    package_dir={"": "."},
    include_package_data=True,
    package_data={
        "crace": ["templates/*", "examples/*", "settings/*.json", "scripts/*"],
    },
    entry_points={
        'console_scripts': [
            'crace_plot=crace_plot.scripts:crace_plot',
        ],
    },
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.1.2",
        "plotly>=5.0.0",
        "matplotlib>=3.5.0",
        "scikit_posthocs>=0.8.0",
        "seaborn>=0.12.0",
        "setuptools>=72.0.0",
        "statannotations>=0.6.0",
        "wheel>=0.40.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    cmdclass={
        'sdist': CustomSDist,
        'bdist_wheel': _bdist_wheel,
    },
)
