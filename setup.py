import sys

from setuptools import setup

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


# ensure that installation is being attempted by an interpreter whose version 
# is gte 3.0, as we rely on Python 3 features
if sys.version_info <= (3, 3):
    sys.exit(
        "The podstar package only supports Python >= 3.3. " \
        "The current interpreter is at version " \
        "{ver.major}.{ver.minor}.{ver.micro}".format(ver=sys.version_info))

setup(
    name = 'podstar',
    packages = ['podstar'],
    version = '0.1.0',
    description = 'An RSS-compatible podcast feed client.',
    author = 'Kenneth Keiter',
    author_email = 'ken@kenkeiter.com',
    url = 'https://github.com/kenkeiter/podstar',
    download_url = 'https://github.com/kenkeiter/podstar/archive/0.1.0.tar.gz',
    keywords = ['rss', 'podcast', 'feed'],
    classifiers = [],
    scripts=['bin/podstar'],
    install_requires=parse_requirements('requirements.txt'),
)