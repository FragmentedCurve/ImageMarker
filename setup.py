from setuptools import setup

setup(
    name='ImageMarker',
    #version='git',
    scripts=['ImageMarker.py'],
    entry_points={'console_scripts': ['ImageMarker = ImageMarker:main']}
)
