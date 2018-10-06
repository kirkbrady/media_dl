'''This sets for media_dl'''
from setuptools import setup

setup(
    name='MediaDL',
    version='1.0',
    py_modules=['media_dl'],
    install_requires=[
        'Click',
        'pytube'
    ],
    entry_points='''
        [console_scripts]
        dl=media_dl:main
    '''
)
