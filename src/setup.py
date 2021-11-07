from setuptools import setup

setup(name='bobs',
      version='0.1',
      description='A Bitcoin observatory to monitor and scan given customizable filters',
      url='https://github.com/PulpCattel/Bobs',
      zip_safe=False,
      packages=['bobs'],
      python_requires=">=3.8",
      install_requires=['aiohttp[speedups]', 'orjson', ' types-chardet', ' types-toml', 'types-orjson',
                        'types-tabulate', 'marshmallow', 'tqdm', 'tabulate', 'psutil'],
      extras_require={
          'jupyter': ['jupyterlab', 'ipython', 'pandas', 'numpy', 'matplotlib', 'pyarrow'],
          'dev': ['hypothesis', 'pytest', 'pytest-asyncio', 'mypy', 'pylint']},
      entry_points={'console_scripts': ['bobs=bobs.main:main']},
      )
