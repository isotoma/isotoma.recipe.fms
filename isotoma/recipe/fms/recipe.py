from glob import glob
import logging
import os
import re
import shutil
import setuptools
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
        
        # add regexp for replacing values in the config file
        self.reg_exp ='\n%s =(.*?)\n'
        
        # set the paths we'll need
        self.options['install_location'] = os.path.join(buildout['buildout']['parts-directory'], self.name) # where we'll install the FMS to
        self.options['bin-directory'] = buildout['buildout']['bin-directory'] # where the bin/control scripts should live

    def set_defaults(self, installed_location):
        # set the options defaults for ourselves
        self.options.setdefault('live_dir', os.path.join(installed_location, 'live'))
        self.options.setdefault('vod_common_dir', os.path.join(installed_location, 'vod'))
        self.options.setdefault('vod_dir', os.path.join(installed_location, os.path.join(installed_location, 'media')))
        self.options.setdefault('appsdir', os.path.join(installed_location, 'applications'))
        self.options.setdefault('js_scriptlibpath', os.path.join(installed_location, 'scriptlib'))
        self.options.setdefault('log_dir', '')
        
    def install(self):
        """ Install the FMS, using the options in the buildout """
        
        # the cache dir to save our downloads to
        download_dir = self.buildout['buildout']['download-cache']
        
                # if the destination already exists, don't reinstall it
        # just update the configs and such
        if not os.path.exists(self.options['install_location']):
        
            # first, we need something to install
            tarball = self.get_tarball(self.options['download_url'], download_dir)
        
            # now we have the code, we need to extract it
            installed_location = self.install_tarball(download_dir, tarball, self.options['install_location'])
        else:
            # if not, we still need to know where it _was_ installed to
            installed_location = self.options['install_location']
        
        self.set_defaults(installed_location)
        
        # now we have some installed software, we need to add the services directory
        self.add_services(installed_location)
        
        # once we have the services directory, we need to alter the fmsmgr script so it knows where they live
        self.alter_fmsmgr(installed_location)
        
        # now we need to update the default config with the options that we have set
        self.create_config(installed_location, self.options)
       
        # now we need to link the system files that we're going to need
        self.create_library_links(installed_location)

        # now add the control script to bin, so we can do something with it
        self.create_bin_file(installed_location, self.options['bin-directory'])
        
    def create_library_links(self, installed_location):
        """ Link the system files that we need to the installed location """
        file_name = os.path.join(installed_location, 'libcap.so.*') 
        if not glob(file_name):
            # Next 2 lines borrowed from ctypes.util source since
            # ctypes.util.find_library doesn't give us the full path on *nix
            expr = r'/[^\(\)\s]*(libcap\.[^\(\)\s]*)'
            res = re.search(expr, 
                            os.popen('/sbin/ldconfig -p 2>/dev/null').read())
            if res:
                file_name = os.path.join(installed_location, res.group(1))
                os.symlink(res.group(0), file_name)

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
        if not os.path.exists(services_dir):
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
        fmsmgr_new = fmsmgr.replace('/etc/adobe/fms/services', os.path.join(installed_location + '/services'))
        
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
        
        def set_ini_option(ini_data, key, value):
            ini_data, replaced = re.subn(self.reg_exp % (re.escape(key),), '\n%s = %s\n' % (key, value), ini_data)
            if not replaced:
                ini_data = ini_data + '\n%s = %s\n' % (key, value)

            return ini_data
        
        # normal config options
        fms_ini = set_ini_option(fms_ini, 'SERVER.ADMIN_USERNAME', options['admin_username'])
        fms_ini = set_ini_option(fms_ini, 'SERVER.ADMIN_PASSWORD', options['admin_password'])

        # join these two together into the format for the config file
        admin_host_and_ip = options['adminserver_interface'] + ":" + options['adminserver_hostport']
        fms_ini = set_ini_option(fms_ini, 'SERVER.ADMINSERVER_HOSTPORT', admin_host_and_ip)
        
        fms_ini = set_ini_option(fms_ini, 'SERVER.PROCESS_UID', options['process_uid'])
        fms_ini = set_ini_option(fms_ini, 'SERVER.PROCESS_GID', options['process_gid'])
        fms_ini = set_ini_option(fms_ini, 'SERVER.LICENSEINFO', options['licenseinfo'])
        fms_ini = set_ini_option(fms_ini, 'SERVER.HTTPD_ENABLED', options['httpd_enabled'].lower())
        
        # join these two together into the format for the config file
        host_and_ip = options['interface'] + ":" + options['hostport']
        fms_ini = set_ini_option(fms_ini, 'ADAPTOR.HOSTPORT', host_and_ip)
        
        # directory based config options (these will default to the installed directory)
        fms_ini = set_ini_option(fms_ini, 'LIVE_DIR', options['live_dir'])
        fms_ini = set_ini_option(fms_ini, 'VOD_COMMON_DIR', options['vod_common_dir'])
        fms_ini = set_ini_option(fms_ini, 'VOD_DIR', options['vod_dir'])
        fms_ini = set_ini_option(fms_ini, 'VHOST.APPSDIR', options['appsdir'])
        fms_ini = set_ini_option(fms_ini, 'APP.JS_SCRIPTLIBPATH', options['js_scriptlibpath'])
        
        # directory based config options (these will default to the installed directory)
        fms_ini = set_ini_option(fms_ini, 'LOGGER.LOGDIR', options['log_dir'])
    
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
        target_path = os.path.join(bin_directory, 'fmsmgr')
        
        shutil.copy(source_path, target_path)
        
        return target_path

    def update(self):
        self.set_defaults(self.options['install_location'])
        # now we need to update the default config with the options that we have set
        self.create_config(self.options['install_location'], self.options)
