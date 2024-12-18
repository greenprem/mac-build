from setuptools import setup

APP = ['tiktokv2.py']
DATA_FILES = []  # Add any additional files if needed
OPTIONS = {
    'argv_emulation': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
