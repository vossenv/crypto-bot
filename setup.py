import os

from setuptools import setup, find_packages

from crypto_bot._version import __version__

def package_files(*dirs):
    paths = []
    for d in dirs:
        for (path, directories, filenames) in os.walk(d):
            for filename in filenames:
                paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('crypto_bot/resources')
setup_deps = [
                 'wheel',
                 'twine'
             ],
setup(name='crypto-bot',
      version=__version__,
      description='Crypto Info Bot',
      long_description='',
      long_description_content_type="text/markdown",
      classifiers=[],
      url='https://github.com/vossenv/crypto-bot',
      maintainer='Danimae Vossen',
      maintainer_email='vossen.dm@gmail.com',
      license='MIT',
      packages=find_packages(),
      package_data={
          'crypto_bot': extra_files,
      },
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
      # entry_points={
      #     'console_scripts': [
      #         'crypto_bot = crypto_bot.app',
      #     ]
      # },
      setup_requires=setup_deps,
      )
