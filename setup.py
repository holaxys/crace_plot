import setuptools

setuptools.setup(
    name="crace-plot",
    packages=["plot"],
    version=0.1,
    python_requires=">=3.6",
    install_requires=[
        'pandas>=1.0.5, <=1.1.5'
    ]
)
