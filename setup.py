from setuptools import setup, find_packages

setup(
    name='SensorProcessor',
    version='0.0.1',
    url='https://github.com/xMinh129/SensorProcessor.git',
    python_requires='>=2.7, <3',
    packages=find_packages(),
    tests_require=['pytest==3.0.3'],
    install_requires=['redis==2.10.6',
                      'cryptography==2.6.1'
                      ]
)
