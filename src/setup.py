"""
Bobs setup file.
"""

from setuptools import setup

REQUIRED_DEPS = [
    'aiohttp[speedups]', 'orjson', ' types-chardet', ' types-toml', 'types-orjson', 'typing-extensions',
    'types-tabulate', 'marshmallow', 'tqdm', 'tabulate', 'psutil'
]
EXTRA_DEPS = {
    'jupyter': ['jupyterlab', 'ipython', 'pandas', 'numpy', 'matplotlib', 'pyarrow'],
    'dev': ['hypothesis', 'pytest', 'pytest-asyncio', 'mypy', 'pylint']
}

setup(name='bobs',
      version='0.1',
      description='A Bitcoin observatory to monitor and scan given customizable filters',
      url='https://github.com/PulpCattel/Observatory',
      project_urls={
          "Bug Tracker": "https://github.com/PulpCattel/Observatory/issues",
      },
      classifiers=[
          "Programming Language :: Python :: 3",
          "Development Status :: 4 - Beta",
      ],
      zip_safe=False,
      packages=['bobs'],
      python_requires=">=3.8",
      install_requires=REQUIRED_DEPS,
      extras_require=EXTRA_DEPS,
      entry_points={'console_scripts': ['bobs=bobs.main:main']},
      )
