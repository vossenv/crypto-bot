import os

from setuptools import setup, find_packages

from crypto_bot._version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()


def package_files(*dirs):
    paths = []
    for d in dirs:
        for (path, directories, filenames) in os.walk(d):
            for filename in filenames:
                paths.append(os.path.join('..', path, filename))
    return paths


# extra_files = package_files('spypi/resources')
# extra_files.extend(package_files('spypi/lib'))
setup_deps = [
                 'wheel',
                 'twine'
             ],
setup(name='crypto-bot',
      version=__version__,
      description='Crypto Info Bot',
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[],
      url='https://github.com/vossenv/crypto-bot',
      maintainer='Danimae Vossen',
      maintainer_email='vossen.dm@gmail.com',
      license='MIT',
      packages=find_packages(),
      # package_data={
      #     'spypi': extra_files,
      # },
      install_requires=[
          'discord',
          'pyyaml',
          'schema',
          'Flask',
          'Werkzeug',
          'requests'
      ],
      extras_require={
          'setup': setup_deps,
      },
      setup_requires=setup_deps,
      )
