import unittest
import tempfile
import os

from recipe import Recipe

class RetrivalTests(unittest.TestCase):
    """ Test retrieving and extracting the FMS tarball """
    
    def setUp(self):
        """ Set up some defaults, and create an instance of the recipe, with enough mock buildout config to get by """
        
        self.download_dir = tempfile.mkdtemp()
        self.eggs_directory = tempfile.mkdtemp()
        self.destination = os.path.join(tempfile.mkdtemp(), 'INSTALLED')
        self.download_url = "http://localhost/~tomwardill/FlashMediaServer4_x64.tar.gz"
        
        # create the recipe, with some mock/temporary buildout config parameters
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
        
    def testExtraction(self):
        """ Test that we can extract a tarball, and move it to the correct directory """
        tarball = self.recipe.get_tarball(self.download_url, self.download_dir)
        
        extracted = self.recipe.install_tarball(self.download_dir, tarball, self.destination)
        
        self.assertTrue(os.path.exists(extracted))
        
    def testServiceCreation(self):
        
        installed_locations = self.recipe.add_services(tempfile.mkdtemp())
        
        for location in installed_locations:
            self.assertTrue('services' in location)
            self.assertTrue(os.path.exists(location))
            
    def testFixFMSMGR(self):
        
        # we need something to work with
        tarball = self.recipe.get_tarball(self.download_url, self.download_dir)
        
        extracted = self.recipe.install_tarball(self.download_dir, tarball, self.destination)
        
        path = self.recipe.alter_fmsmgr(self.destination)
        
        f = open(path).read()
        self.assertTrue(self.destination in f)
        
    def testFixConfig(self):
        """ Fix the config files with the options that we give """
        
        tarball = self.recipe.get_tarball(self.download_url, self.download_dir)
        
        extracted = self.recipe.install_tarball(self.download_dir, tarball, self.destination)
        
        options = {}
        options['admin_username'] = "foo"
        options['admin_password'] = "foo"
        options['adminserver_hostport'] = "foo"
        options['process_uid'] = "foo"
        options['process_gid'] = "foo"
        options['licenseinfo'] = "foo"
        options['httpd_enabled'] = "foo"
        options['hostport'] = "foo"
        options['live_dir'] = "foo"
        options['vod_common_dir'] = "foo"
        options['vod_dir'] = "foo"
        options['appsdir'] = "foo"
        options['js_scriptlibpath'] = "foo"
        
        locations = self.recipe.create_config(self.destination, options)
        
        for loc in locations:
            f = open(loc).read()
            self.assertTrue('foo' in f)