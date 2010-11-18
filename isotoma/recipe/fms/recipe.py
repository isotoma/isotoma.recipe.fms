import logging
import os
import urllib2
import shutil

import zc.recipe.egg
import setuptools

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
        # now we have that, we need to extract it
        installed_location = self.install_tarball(download_dir, tarball, self.options['install_location'])
        
        # set the options defaults for ourselves
        self.options.setdefault('live_dir', os.path.join(installed_location, 'live'))
        self.options.setdefault('vod_common_dir', os.path.join(installed_location, 'vod'))
        self.options.setdefault('vod_dir', os.path.join(installed_location, os.path.join(installed_location, 'media')))
        self.options.setdefault('appsdir', os.path.join(installed_location, 'applications'))
        self.options.setdefault('js_scriptlibpath', os.path.join(installed_location, 'scriptlib'))
        
        # now we have some installed software, we need to add the services directory
        self.add_services(installed_location)
        
        # once we have the services directory, we need to alter the fmsmgr script so it knows where they live
        self.alter_fmsmgr(installed_location)
        
        # now we need to update the default config with the options that we have set
        self.create_config(installed_location, self.options)
        
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
    
    def install_tarball(self, download_dir, tarball, destination):
        """ Extract the given tarball, and move the contents to the correct destination
        
        Arguments:
        download_dir -- The directory where the tarball was downloaded to. This will be used to extract it
        tarball -- The path to the downloaded tarball
        destination -- The path to move the extracted contents to
        
        Returns the path to the moved files
        """
        
        # extract the tarball to somewhere where we can get it
        extraction_dir = os.path.join(download_dir, 'fms-archive')
        setuptools.archive_util.unpack_archive(tarball, extraction_dir)
        
        # the name of the extracted dir may change, as it has a version number in it
        # however, we can reasonably hope that it's the only directory in there
        # so get the first dir in there, and use that
        untarred_dir = os.path.join(extraction_dir, os.listdir(extraction_dir)[0])
        
        # move the extracted dir to our destination
        shutil.move(untarred_dir, destination)
        
        # remove the extracted files, we don't need it anymore
        shutil.rmtree(extraction_dir)
        
        return destination
    
    def add_services(self, installed_location):
        """ Add the services information required for FMS startup
        
        Arguments:
        installed_location -- The location that FMS was extracted/installed to
        
        Returns a list of paths to the services created
        """
        
        # The services are text files in the 'services' folder in the installed FMS folder
        # We will need to create the folder, then add the services lines as required
        
        services_dir = os.path.join(installed_location, 'services')
        os.makedirs(services_dir)
        
        # now we have the folder, we need to populate it
        # the fms service contains a path to the installed_location
        fms_service = os.path.join(services_dir, 'fms')
        fms_file = open(fms_service, 'w')
        fms_file.write(installed_location)
        fms_file.close()
        
        # the admin service only contains the word 'fms'
        fmsadmin_service = os.path.join(services_dir, 'fmsadmin')
        fmsadmin_file = open(fmsadmin_service, 'w')
        fmsadmin_file.write('fms')
        fms_file.close()
        
        return [fms_service, fmsadmin_service]
    
    def alter_fmsmgr(self, installed_location):
        """ Alter the fmsmgr script, replacing the services location with the one where we installed the services to
        
        Arguments:
        installed_location -- The location that FMS was extracted/installed to
        
        Returns the path to the fmsmgr script
        """
        
        # we need to get the fmsmgr script so we can edit it
        fmsmgr_path = os.path.join(installed_location, 'fmsmgr')
        fmsmgr_file = open(fmsmgr_path, 'r')
        fmsmgr = fmsmgr_file.read()
        fmsmgr_file.close()
        
        # now replace the inbuilt path to the services with our installed ones
        fmsmgr_new = fmsmgr.replace('/etc/adobe/fms/services', installed_location)
        
        # now we need to write that out again
        fmsmgr_file = open(fmsmgr_path, 'w')
        fmsmgr_file.write(fmsmgr_new)
        fmsmgr_file.close()
        
        return fmsmgr_path
    
    def create_config(self, installed_location, options):
        """ Alter the config file with the options that we have set
        
        Arguments:
        installed_location -- The location that FMS was extracted/installed to
        options -- The options that we need for the config file
        
        Returns a list of the paths to the config files that were changed
        """
        
        # get the fms.ini from the config dir of the installed FMS
        conf_dir = os.path.join(installed_location, 'conf')
        fms_path = os.path.join(conf_dir, 'fms.ini')
        
        # read in the fms.ini so we can do some manipulation
        fms_file = open(fms_path, 'r')
        fms_ini = fms_file.read()
        fms_file.close()
        
        # normal config options
        fms_ini = fms_ini.replace('SERVER.ADMIN_USERNAME =', 'SERVER.ADMIN_USERNAME = ' + options['admin_username'])
        fms_ini = fms_ini.replace('SERVER.ADMIN_PASSWORD =', 'SERVER.ADMIN_PASSWORD = ' + options['admin_password'])
        fms_ini = fms_ini.replace('SERVER.ADMINSERVER_HOSTPORT =', 'SERVER.ADMINSERVER_HOSTPORT = ' + options['adminserver_hostport'])
        fms_ini = fms_ini.replace('SERVER.PROCESS_UID =', 'SERVER.PROCESS_UID = ' + options['process_uid'])
        fms_ini = fms_ini.replace('SERVER.PROCESS_GID =', 'SERVER.PROCESS_GID = ' + options['process_gid'])
        fms_ini = fms_ini.replace('SERVER.LICENSEINFO =', 'SERVER.LICENSEINFO = ' + options['licenseinfo'])
        fms_ini = fms_ini.replace('SERVER.HTTPD_ENABLED =', 'SERVER.HTTPD_ENABLED = ' + options['httpd_enabled'].lower())
        fms_ini = fms_ini.replace('ADAPTOR.HOSTPORT =', 'ADAPTOR.HOSTPORT = :' + options['hostport'])
        
        # directory based config options (these will default to the installed directory)
        fms_ini = fms_ini.replace('LIVE_DIR =', 'LIVE_DIR = ' + options['live_dir'])
        fms_ini = fms_ini.replace('VOD_COMMON_DIR =', 'LIVE_DIR = ' + options['vod_common_dir'])
        fms_ini = fms_ini.replace('VOD_DIR =', 'LIVE_DIR = ' + options['vod_dir'])
        fms_ini = fms_ini.replace('VHOST.APPSDIR =', 'LIVE_DIR = ' + options['appsdir'])
        fms_ini = fms_ini.replace('APP.JS_SCRIPTLIBPATH =', 'LIVE_DIR = ' + options['js_scriptlibpath'])
    
        # write out the new fms ini
        fms_file = open(fms_path, 'w')
        fms_file.write(fms_ini)
        fms_file.close()
        
        return [fms_path]
    
    def create_bin_file(self, installed_location, bin_directory):
        """ Create the bin file in the correct place
        
        Arguments:
        installed_location -- The location that FMS was extracted/installed to
        bin_directory -- The location of the bin directory to install file to
        
        Returns the path to the bin file
        """
        
        # In theory, the fsmmgr file is all the management file that we need
        # so we can pull our modified one out of the installed directory
        # and put it in the bin dir.
        # This should then behave correctly.
        
        source_path = os.path.join(installed_location, 'fmsmgr')
        target_path = os.path.join(installed_location, 'fmsmgr')
        
        shutil.copy(source_path, target_path)
        
        return target_path
