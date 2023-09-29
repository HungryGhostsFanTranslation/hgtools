from setuptools import setup, find_packages

setup(
    name='hgtools',
    version='0.0.1',
    packages=find_packages(),
    py_modules=['hgtools'],
    install_requires=[
        'Click',
        'kaitaistruct'
    ],
    entry_points={
        'console_scripts': [
            'hgtools = hgtools.main:cli',
        ],
    },
)