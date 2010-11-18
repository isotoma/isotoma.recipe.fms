
import zc.recipe.egg
import setuptools

class Recipe(object):
    """ The main recipe object, this is the one that does stuff """
    
    def __init__(self, buildout, name, options):
        """ Set up the options and paths for the recipe """
        