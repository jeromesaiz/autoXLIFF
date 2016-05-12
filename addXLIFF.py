#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__description__ = 'A companion tool to autoXLIFF.py. Helps batch-add translation strings to existing XLIFF documents (useful to add arbitrary strings like those that appear in files other than twig templates, since those are not picked-up automatically by autoXLIFF. Example : form labels in controllers'
__author__ = 'Jerome Saiz (https://twitter.com/jeromesaiz)'
__version__ = '0.0.1'
__date__ = '2016/05/12'

# Coloring definition
INFO = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

import os
import sys
import re
import argparse
try:
  from lxml import etree
except ImportError:
  print FAIL+'FATAL : '+ENDC+' This programm requires the lxml module. Please '+INFO+'pip install lxml'+ENDC
  sys.exit(1)


# Define command-line arguments
# @input : VOID
# @return : argparse.Namespace
def get_args():
  parser = argparse.ArgumentParser(description='A companion tool to autoXLIFF.py. Helps batch-add translation strings to existing XLIFF files.')
  parser.add_argument("app_path", help="Absolute path to your web application root directory", type=str, )
  parser.add_argument("source", help="Absolute path to source file storing the translation tokens to add", type=str, )
  parser.add_argument("locfile", help="Locale file to be edited (if no extension provided will search for .xlf and .xliff files as well)", type=str, )
  parser.add_argument("--locdir", help="Relative path to your localization files within the web application directory structure (default to locales/)", type=str, )
  parser.add_argument("--dry", help="Dry run mode : do not commit any change to files, only output the modified XLIFF to screen", action="store_true", )
  return parser.parse_args()


# Process command-line arguments to validate path, determine full paths, etc...
# @input argparse.Namespace
# @return LIST (STR path to localization file, FILE (descriptor for language file opened from disk)
def get_setup(args):
  if not os.path.exists(args.app_path):
    print FAIL+'FATAL : '+ENDC+args.app_path+' does not seem to be workable. Try another directory.'
    sys.exit(1)

  # determine the localization files directory
  if args.locdir:
    locpath = os.path.join(args.app_path,args.locdir)
  else:
    locpath = os.path.join(args.app_path,'locales')

  # determine locfile full path. We also look for .xlf or .xliff extensions if not provided
  locfile = os.path.normpath(os.path.join(locpath,args.locfile))
  try:
    f = open(locfile, "r+")
  except IOError:
    try:
      f = open(locfile+'.xlf', "r+")
      locfile = locfile+'.xlf'
    except IOError:
      try:
        f = open(locfile+'.xliff', "r+")
        locfile = locfile+'.xliff'
      except IOError:
        # localization file does not exist. It will need to be created first with autoXLIFF
        print FAIL+'FATAL : '+ENDC+locfile+' does not seem to exist. Try running autoXLIFF first.'
        sys.exit(1)

  # check for source file
  if not os.path.isfile(args.source):
    print FAIL+'FATAL : '+ENDC+'Source file '+args.source+' does not seem to exist. Try another path or create it first.'
    sys.exit(1)

  return locfile,f

def get_source(sourcefile):
  tokens = [line.rstrip('\n') for line in open(sourcefile,'r')]
  if not tokens:
    print FAIL+'FATAL : '+ENDC+'Source file '+args.source+' is empty. Please add translation tokens.'
    sys.exit(1)
  return tokens


# Loads a XLIFF structure from file and does a quick validation
# @intput STRING (absolute path to XLIFF language file to load)
# @return False if file is no XML or not XLIFF
# @return object (etree Element) as XML root if content is valid XLIFF
# @return STRING as XLIFF namespace of document or None if importation triggered an error
def load_xliff(xml_content):
  try:
    xml = etree.parse(xml_content)
    root = xml.getroot()
    try:
      ns = re.search(r'({.*})xliff', root.tag).group(1) # extract existing namespace, if any
    except AttributeError:
      ns = ''

  except:
    print 'Error : XML import failed (from file '+xml_content+')'
    print  'Message : ',
    except_class,except_message,except_tb = sys.exc_info()
    print except_message
    return False,None

  return root,ns

# Gets a list of all trans-units already defined within the loaded XML object
# @input object (Element) representing the XLIFF root
# @input STRING as the XLIFF namespace
# @return SET (list of existing trans-units)
def get_trans_units(root,ns):
  trans=set()
  for elem in root.iter(tag=ns+'trans-unit'):
    trans.add(elem.attrib.get('id'))
  print 'Found a total of '+str(len(trans))+' trans keywords already defined in your XLIFF file'
  return trans

# Remove existing transunits from source file
# @input SET (list of existing trans-units within the XLIFF language file)
# @input LIST (list of new trans-unit keywords to add, coming from source file)
# @return SET (new list of trans-unit keywords without doubles)
def prune(trans,keywords):
  doubles = trans & set(keywords)
  for elem in doubles:
    keywords.remove(elem)
  return set(keywords)


# Adds trans keywords to XML structure from source file and writes it back
# @input object (Element) representing XLIFF root
# @input STRING as the XLIFF namespace
# @input SET (list of existing trans-units within the XLIFF language file)
# @input SET (list of new trans-unit keywords to add)
# @input STRING (path to XLIFF file)
# @input FILE (file descriptor to XLIFF file)
# @input argparse.Namespace
# @return VOID
def update_locfile(root,ns,trans,keywords,locfile,f,args):

  print "\nOperations :"

  # Add the new trans-units
  for elem in root.iter(tag=ns+'body'): #ugly hack to skip over other elements between root and body
    body = elem

  # Create the new trans-unit elements
  for transunit in keywords:
    tu = etree.SubElement(body,'trans-unit', id=transunit)
    so = etree.SubElement(tu,'source')
    ta = etree.SubElement(tu,'target')
    so.text = transunit
    print '\t'+OK+'adding\t\t'+ENDC, transunit

  # Attach our root to a new XML structure
  xml = etree.ElementTree(root)

  # And write it back !

  # ... to stdout if in dry run mode
  if args.dry:
    print '\nDumping file (dry run mode) :\n-------- XML file dump --------'
    xml.write(sys.stdout, encoding="utf-8", xml_declaration=True)
    print '\n-------------------------------\n'
  # ... or to disk
  else:
    # create file for writing if it does not exist, or clear existing file from existing content
    if None == f:
      f = open(locfile,'w')
    else:
      os.ftruncate(f.fileno(), 0)
      os.lseek(f.fileno(), 0, os.SEEK_SET)
    # And write it
    try:
      xml.write(f, encoding="utf-8", xml_declaration=True)
      f.close()
      print INFO+'\nDone !'+ENDC+' File saved. Now go translate those strings !\n'
    except IOError:
      print FAIL+'FATAL : '+ENDC+' could not write back to file '+locfile


# Let's go !
def Main():
  args = get_args()
  setup = get_setup(args)

  locfile = setup[0]
  f = setup[1] # file descriptor of language file

  # load XLIFF either from existing file or empty structure as string
  root,ns = load_xliff(locfile)

  # get existing trans-units from XLIFF object
  trans = get_trans_units(root,ns)

  # get news trans-units to add from source file
  keywords = get_source(args.source)

  # remove existing transunits from source
  keywords = prune(trans,keywords)

  # Update language file
  update_locfile(root,ns,trans,keywords,locfile,f,args)

# Execute
if __name__ == '__main__':
  Main()
