#!/usr/bin/python

# Copyright (c) 2011 Netcetera.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# MIT License: http://www.opensource.org/licenses/mit-license.php
#
# Contributors:
#    Netcetera AG
#    Michael Pellaton
#

import glob
import os
import re
import shutil
import subprocess

REL_PATH_SRC_DIR = 'source'
REL_PATH_WORK_DIR = 'work'
REL_PATH_TARGET_DIR = 'target'

def _read_file_and_join_lines(file_name):
  '''
  Reads all contents of a file and appends each line into one ',' separated string. 
  Leading and trailing whitespace is removed. Lines having a '#' character as first non-
  whitespace character are considered as comment and are therefore ignored in the output. 
  @param fileName: the file to read
  '''
  
  def _normalizeString(line):
    return line.replace('\n', '').strip()

  def _isComment(line):
    return not line.startswith("#")
  
  def _isEmptyLine(line):
    return line != ""
  
  with open(file_name, 'r') as file:
    return ','.join(filter(_isEmptyLine, filter(_isComment, map(_normalizeString, file.readlines()))))  


def _get_tag_name(iulist):
  '''
  Gets the tag name of the iulist which is the file name excluding the leading sort number and 
  the trailing iulist extension.
  @param iulist: the file name to get the tag name from 
  '''
  parts = iulist.split('.')
  if len(parts) == 3:
    return parts[1]
  return 'unknown'

def _get_distribution_info(source_dir, work_dir):
  '''
  Finds all Eclipse SDK archives in 'dowloadDir' and extracts the information used from the filename.
  '''
  distribution_info = []
  for distribution in glob.glob(os.path.join(source_dir, 'eclipse-SDK-*')):
    a, b, s, v, variant = distribution.split('-', 4)
    platform, filetype = variant.split('.', 1)
    distribution_info.append((os.path.abspath(distribution), platform, filetype, 
                             os.path.abspath(os.path.join(work_dir, platform))))
  return distribution_info


def _extract_archive(archivefile, filetype, platform_workdir):
  '''
  Extracts the Eclipse archive file into a working directory.
  @param archivefile: the archive file to extract
  @param filetype: the file type of the archive
  @param platform_workdir: the platform working directory where the archive shall be extracted
  '''
  if os.path.exists(platform_workdir):
    shutil.rmtree(platform_workdir)
  os.mkdir(platform_workdir)
  
  if filetype == 'tar.gz':
    _call_executable(['tar', '-xzf', archivefile], platform_workdir)
  elif filetype == 'zip':
    _call_executable(['unzip', archivefile], platform_workdir)
  else:
    print('Error: unknown file type \'{ftype}\''.format(ftype=filetype))
    exit(-1)


def _create_archive(platform_workdir, filetype, platform, distribution_name, target_dir):
  '''
  Creates an archive of the type specified.
  @param platform_workdir: the working directory to create an archive from
  @param filetype: the file type of the archive
  @param platform: the platform string
  @param distribution_name: the name of the distribution 
  '''
  archiveFile = os.path.join(os.path.abspath(target_dir), distribution_name + '-' + platform + '.' + filetype)
  
  if os.path.exists(archiveFile):
    os.remove(archiveFile)
    
  if filetype == 'tar.gz':
    _call_executable(['tar', '-czf', archiveFile, distribution_name], platform_workdir)
  elif filetype == 'zip':
    _call_executable(['zip', '-r', archiveFile, distribution_name], platform_workdir)
  else:
    print('Error: unknown file type \'{ftype}\''.format(ftype=filetype))
    exit(-1)


def _install(destination, configpath, eclipse_binary):
  '''
  Installs the IUs into Eclipse.
  @param destination: the eclipse to install to
  @param configpath: the path to the directory containing the iu and repo lists
  @param eclipse_binary: the Eclipse binary used as installer
  '''
  iulist_list = glob.glob(os.path.join(configpath, '*.iulist'))
  iulist_list.sort()
  for iulist in iulist_list :
    repolist = iulist.replace('.iulist', '.repolist');
    if os.path.exists(repolist):
      print('  -IUs: ' + iulist + ' from: ' + repolist)
      _call_executable([os.path.abspath(eclipse_binary), 
                        '-application', 'org.eclipse.equinox.p2.director', 
                        '-repository', _read_file_and_join_lines(repolist), 
                        '-installIU', _read_file_and_join_lines(iulist),
                        '-destination', destination,
                        '-tag', _get_tag_name(iulist),
                        '-profile', 'SDKProfile'])
  

def _call_executable(commandline, command_workdir=os.getcwd()):
  '''
  Executes an operating system command.
  @param commandline: the command line to execute
  @param command_workdir: the working directory of the command (optional)
  '''
  with open(os.devnull, 'w') as devnull:
    returncode = subprocess.call(commandline, cwd=command_workdir, stdout=devnull)
    if not returncode == 0:
      print('I am terribly sorry but due to an error this run was aborted.')
      exit(returncode)


def _manipulate_splash(basedir, distribution_description):
  '''
  Writes the distribution description into the splash.bmp file
  @param basedir: the base directory in which to look for the splash file  
  @param distribution_description the textual name to be printed into the splash screen
  '''
  splash_files = glob.glob(basedir + '/plugins/org.eclipse.platform*/splash.bmp')
  if not len(splash_files) == 1: 
    print('Error: splash.bmp not found in {d}'.format(d=basedir))
    exit(-1)
  # FIXME 2011-08-22 michael.pellaton: use two Popen objects connected via PIPE...
  os.popen('convert -background \'#00000000\' -pointsize 14 -font Nimbus-Sans-Regular -fill white label:\'{d}\' miff:- | composite -gravity northeast  -geometry +62+10 - {f} {f}'.format(d=distribution_description, f=os.path.abspath(splash_files[0])))


def assemble(configpath, distribution_name, distribution_description, eclipse_binary):
  # Make sure the download dir exists.
  download_dir = os.path.abspath(os.path.join(configpath, REL_PATH_SRC_DIR))
  if not (os.path.exists(download_dir) and os.path.isdir(download_dir)):
    exit('The download source directory does not exist: {dir}'.format(dir=download_dir))
  
  # Make sure the work dir exists. Delete and re-create it if it exists.
  work_dir = os.path.abspath(os.path.join(configpath, REL_PATH_WORK_DIR))
  if os.path.exists(work_dir):
    _call_executable(['rm', '-rf', work_dir])
  os.mkdir(work_dir)

  # Make sure the target dir exists  
  target_dir = os.path.abspath(os.path.join(configpath, REL_PATH_TARGET_DIR))
  if not os.path.exists(target_dir):
    os.mkdir(target_dir)

    
  for (archive, platform, filetype, platform_workdir) in _get_distribution_info(download_dir, work_dir):
    print('Assembling {dist} for {plat}...'.format(dist=distribution_name, plat=platform))
    print(' -extracting archive')
    _extract_archive(archive, filetype, platform_workdir)
    print(' -renaming target')
    destination = os.path.join(platform_workdir, distribution_name)
    os.rename(os.path.join(platform_workdir, 'eclipse'), destination)
    print(' -installing IUs')
    _install(destination, configpath, eclipse_binary)
    print(' -manipulating splash screen')
    _manipulate_splash(destination, distribution_description)
    print(' -creating archive')
    _create_archive(platform_workdir, filetype, platform, distribution_name, target_dir)
    print(' -done.')
