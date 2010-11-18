import os

from setuptools import setup, find_packages

version = '0.0.1'

def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),
                             name)).read()

readme = read_file('README.rst')
changes = read_file('CHANGES.txt')

setup(name='isotoma.recipe.fms',
      version=version,
      description="Buildout recipe to deploy Flash Media Server",
      long_description='\n\n'.join([readme, changes]),
      classifiers=[
        'Topic :: Software Development :: Build Tools',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        ],
      packages=find_packages(exclude=['ez_setup']),
      keywords='',
      author='Tom Wardill',
      author_email='tom.wardill@isotoma.com',
      url='http://github.com/isotoma',
      license='BSD',
      zip_safe=False,
      install_requires=[
        'zc.buildout',
        'zc.recipe.egg',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [zc.buildout]
      default = isotoma.recipe.fms.recipe:Recipe
      """,
      )
