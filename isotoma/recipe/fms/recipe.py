import logging
import os
import urllib2

import zc.recipe.egg

class Recipe(object):
    """ The main recipe object, this is the one that does stuff """
    
    def __init__(self, buildout, name, options):
        """ Set up the options and paths for the recipe """
        
        # set up some bits for the buildout to use
        self.log = logging.getLogger(name)
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        # set the options we've been passed so that we can get them when we install
        self.buildout = buildout
        self.name = name
        self.options = options
        
        # set the paths we'll need
        options['install_location'] = os.path.join(buildout['buildout']['parts-directory'], self.name) # where we'll install the FMS to
        options['bin-directory'] = buildout['buildout']['bin-directory'] # where the bin/control scripts should live
        
        
    def install(self):
        """ Install the FMS, using the options in the buildout """
        
        # the cache dir to save our downloads to
        download_dir = self.buildout['buildout']['download-cache']
        
        # first, we need something to install
        tarball = self.get_tarball(self.options['download_url'], download_dir)
        
        
        
    def get_tarball(self, download_url, download_dir):
        """ Download the FMS release tarball

        Arguments:
        download_url -- The URL to download the tarball from
        download_dir -- The directory to save the tarball to
        
        Returns a path to the downloaded tarball
        """
        
        target = os.path.join(download_dir, 'FMS_DOWNLOAD.tar.gz')
        
        # if we haven't already got the tarball
        if not os.path.exists(target):
            
            # grab it from the download_url we were given
            tarball = open(target, 'wb')
            download_file = urllib2.urlopen(download_url)
            tarball.write(download_file.read())
            tarball.close()
            download_file.close()
            
        # return the path to the tarball we just downloaded
        return target
        