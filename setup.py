from setuptools import setup, find_packages

setup(
    name='hgtools',
    version='1.1.6',
    packages=find_packages(),
    py_modules=['hgtools'],
    install_requires=[
        'Click',
        "kaitaistruct",
        'pyyaml',
        'defusedxml',
        'pypng',
        'pycdlib',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'hgtools = hgtools.main:cli',
        ],
    },
    include_package_data=True
)
