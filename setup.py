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

with open('README.md', 'r') as fh:
    readme = fh.read()

setup(
    name = 'podstar',
    packages = ['podstar'],
    version = '1.0.0',
    description = 'An RSS-compatible podcast feed client.',
    long_description = readme,
    long_description_content_type = 'text/markdown',
    author = 'Kenneth Keiter',
    author_email = 'ken@kenkeiter.com',
    url = 'https://github.com/kenkeiter/podstar',
    license = 'MIT',
    keywords = ['rss', 'podcast', 'feed'],
    classifiers = [],
    python_requires='>=3.3',
    install_requires=parse_requirements('requirements.txt'),
)