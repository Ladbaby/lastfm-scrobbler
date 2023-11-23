from os import path
from setuptools import setup, find_packages

root = path.abspath(path.dirname(__file__))
with open(path.join(root, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='lastfm-mpris2-scrobbler',
    version='1.0.3',
    description="Last.fm scrobbler via MPRIS2 in Linux",
    url="https://github.com/Ladbaby/lastfm-scrobbler",
    author="Ladbaby",
    author_email="Ladbabyms@outlook.com",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "coloredlogs",
        "mpris2",
        "pylast",
        "PyYAML",
        "dbus-python",
        "pyxdg",
    ],
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "lastfm-mpris2-scrobbler = lastfm_mpris2_scrobbler.__main__:main",
        ],
    },
    zip_safe=False,
)
