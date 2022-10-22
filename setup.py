"""

"""

from setuptools import find_packages, setup



def get_install_requires():
    install_requires = [
        "PyQt5",
        "qdarkstyle",
        # "requests",
        # "websocket-client",
        "peewee",
        "pymysql",
        "arctic"
        "mongoengine",
        "numpy",
        "pandas",
        "matplotlib",
        # "seaborn",
        "rqdatac",
        "ta-lib",
        "deap",
        "sklearn",
        "statsmodels",
        "toolz",
        "pyqtgraph",
        "dask",
        # "ray",
        "numba",
        # "itchat",
        "psutil",
        # "pyyaml",
        # "nanomsg"
        "futu-api"
    ]
    return install_requires



setup(
    name="pystarquant",
    version='1.0rc2',
    author="physercoe",
    author_email="whereiive@gmail.com",
    license="MIT",
    url="https://github.com/physercoe/starquant",
    description="A framework for developing quant trading systems.",
    long_description=__doc__,
    keywords='quant quantitative investment trading algotrading',
    include_package_data=True,
    packages=find_packages(exclude=["teststrategy", "mystrategy","test","indicator"]),
    install_requires=get_install_requires(),
    package_data={"": [
        "*.gif",
        "*.png",
        "*.yaml",
        "*.ico",
        "*.pyd",
    ]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Operating System :: Microsoft :: Windows :: Windows 8",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows Server 2008",
        "Operating System :: Microsoft :: Windows :: Windows Server 2012",
        "Operating System :: Microsoft :: Windows :: Windows Server 2012",
        "Operating System :: POSIX :: Linux"
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: Chinese (Simplified)"
    ],
)
