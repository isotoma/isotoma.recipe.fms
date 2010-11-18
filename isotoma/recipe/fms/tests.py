import unittest
import tempfile
import os

from recipe import Recipe

class RetrivalTests(unittest.TestCase):
    """ Test retrieving and extracting the FMS tarball """
    
    def setUp(self):
        self.download_dir = tempfile.mkdtemp()
        self.eggs_directory = tempfile.mkdtemp()
        self.download_url = "http://localhost/~tomwardill/FlashMediaServer4_x64.tar.gz"
        
        self.recipe = Recipe({'buildout':{
            'download-cache': self.download_dir, 
            'eggs-directory': self.eggs_directory,
            'develop-eggs-directory': tempfile.mkdtemp(),
            'bin-directory': tempfile.mkdtemp(),
            'parts-directory': tempfile.mkdtemp(),
            'python': 'python'},
            'python': {'executable': 'usr/bin/python'}
            }, 
                             'test-recipe', 
                             {'download_url': self.download_url, 'recipe': 'isotoma.recipe.fms'})
        
    def testDownload(self):
        """ Test that we can download a tarball from a given url """
        
        tarball = self.recipe.get_tarball(self.download_url, self.download_dir)
        
        self.assertTrue(tarball.endswith("FMS_DOWNLOAD.tar.gz"))
        self.assertTrue(os.path.exists(tarball))