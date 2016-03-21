#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__description__ = 'A tool to help developpers create and update their XLIFF translation files automatically from Twig views. Works out of the box with Silex'
__author__ = 'Jerome Saiz (https://twitter.com/jeromesaiz)'
__version__ = '0.0.1'
__date__ = '2016/03/19'

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
  parser = argparse.ArgumentParser(description='A tool to help developpers create and update their XLIFF translation files automatically from Twig views. Works out of box with Silex')
  parser.add_argument("app_path", help="Absolute path to your web application root directory", type=str, )
  parser.add_argument("locfile", help="Locale file to be created or edited (if no extension provided will search for .xlf and .xliff files as well)", type=str, )
  parser.add_argument("--lang", help="Source/destination languages pair to use when *creating* a new localization file (defaults to en/en) ", type=str, )
  parser.add_argument("--locdir", help="Relative path to your localization files within the web application directory structure (default to locales/)", type=str, )
  parser.add_argument("--twigdir", help="Relative path to your Twig views within the web application directory structure (default to views/)", type=str, )
  parser.add_argument("--dry", help="Dry run mode : do not commit any change to files, only output the modified XLIFF to screen", action="store_true", )
  return parser.parse_args()


# Process command-line arguments to determine correct paths, filenames, etc...
# We want to determine paths to :
# 1/ that localization file we need to process (it will be created if it does not exist and its full path returned)
# 2/ the correct Twig views directory
# @input argparse.Namespace
# @return LIST (path to localization file)
# @return LIST (path to Twig views directory)
# @return FILE (descriptor for language file just created or opened from disk)
def get_setup(args):
  if not os.path.exists(args.app_path):
    print FAIL+'FATAL : '+ENDC+args.app_path+' does not seem to be workable. Try another directory.'
    sys.exit(1)

  # determine the Twig views directory
  if args.twigdir:
    twigpath = os.path.join(args.app_path,args.twigdir)
  else:
    twigpath = os.path.join(args.app_path,'views')

  twigdir = os.path.normpath(twigpath)

  # determine the localization files directory
  if args.locdir:
    locpath = os.path.join(args.app_path,args.locdir)
  else:
    locpath = os.path.join(args.app_path,'locales')

  for path in (locpath,twigpath):
      if not os.path.exists(path):
        print FAIL+'FATAL : '+ENDC+path+' does not seem to be workable. Try another directory.'
        sys.exit(1)

  locfile = os.path.normpath(os.path.join(locpath,args.locfile))


  # look for localization file as is, and if we can't find it search for it adding default .xlf or .xliff extensions
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
        # localization file does not exist. It will need to be created
        f = None

  return locfile,twigdir,f


# Create a XLIFF XML structure
# @input argparse.Namespace
# @return FILE (descriptor for language file created)
def create_xliff(args):

  if args.lang:
    lang_pair = args.lang.split('/',2)
    source = lang_pair[0]
    destination = lang_pair[1]
  else:
    source = destination = 'en' # default

  # build simple XLIFF root structure
  new_file="""
<xliff version="1.2">
<file source-language="{0}" target-language="{1}" tool='autoXLIFF' datatype="plaintext" original="{2}">
<body>
</body>
</file>
</xliff>
  """
  print 'Building new XLIFF structure'
  return new_file.format(source,destination,args.locfile)


# Loads a XLIFF structure either from file or string and does a quick validation
# @intput STRING (absolute path to XLIFF language file to load **OR** XLIFF empty structure)
# @return False if file is no XML or not XLIFF
# @return object (etree Element) as XML root if content is valid XLIFF
# @return STRING as XLIFF namespace of document (if imported)
def load_xliff(xml_content):

  # Read content from disk if argument is a valid file
  # Since "fromstring" returns the document's root, we need to return it here too instead of the full XML document
  if os.path.isfile(xml_content):
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

  # Or read it from string
  else:
    try:
      root = etree.fromstring(xml_content)
      ns = ''
    except:
      print 'Error : XML validation failed (from string)'
      except_class,except_message,except_tb = sys.exc_info()
      print except_message
      return False,None

  # check for XLIFF mention in root (lazy validation)
  if not 'xliff' in root.tag:
    print 'Error : does not seem to be a XLIFF format'
    return False,None
  return root,ns


# Iterate on Twig views to locate translation tags to process
# @input STRING (path to Twig views)
# @return LIST (absolute paths to Twig views, parsed recursively)
def twig_explore(twigdir):
  twigfiles = list();
  for dirpath, dirs, files in os.walk(twigdir):
      for filename in files:
        twigfiles.append(os.path.join(dirpath,filename))
  return twigfiles


# Parse a list of Twig files to extract individual trans keywords
# Supports three notations for Twig trans (see readme)
# @input LIST (absolute path to individual Twig templates)
# @return SET (list of all trans keywords found in the templates)
def parse_twig(twigfiles):
  keywords = set()
  pattern = re.compile("{% ?trans ?%}(.*?){% ?endtrans ?%}|{{ ?[\'|\"](.*?)[\'|\"] ?\| ?trans ?}}|{{ ?.*?\.translator\.trans\([\'|\"](.*?)[\'|\"]\) ?}}|{% ?trans ?with.*?}.*%}(.*?){% ?endtrans ?%}|{{ ?[\'|\"](.*?)[\'|\"]\|trans\(.*\) ?}}",
                       re.IGNORECASE)
  # Let's look for matches !
  for file in twigfiles:
    f = open(file,'r') # helps closing the file after looping
    for line in f:
      for match in re.finditer(pattern, line): # allows for matches on the same line
        for this_match in match.groups():
          if this_match != None:
            keywords.add(this_match)
    f.close()

  print 'Found a total of '+str(len(keywords))+' unique trans keywords in your project'
  return keywords


# Gets a list of all trans-units already defined within the language file from loaded XML object
# @input object (Element) representing the XLIFF root
# @return SET (list of existing trans-units)
def get_trans_units(root,ns):
  trans=set()
  for elem in root.iter(tag=ns+'trans-unit'):
    trans.add(elem.attrib.get('id'))
  print 'Found a total of '+str(len(trans))+' trans keywords already defined in your XLIFF file'
  return trans


# Adds or remove trans keywords to/from locfile and writes it back
# @input object (ElementTree) representing XLIFF language file
# @input SET (list of existing trans-units within the XLIFF language file)
# @input SET (list of unique trans-unit keywords located across all Twig views)
# @return VOID
def update_locfile(root,ns,trans,keywords,locfile,f,args):
  to_add=keywords-trans
  to_delete=trans-keywords

  print "\nOperations :"

  # check if file need to be updated
  if len(to_add) == len(to_delete) == 0:
    print 'Nothing to update\n'
    if f:
      f.close()
    return

  # Remove trans-units that are not used in Twig templates anymore
  # This be optimized as we parse & iterate twice on the same XML structure here (see get_trans_units)
  # But this allows to decorrelate the getting of trans-units list and the actual XML structure manipulation
  #trans_units = xml.getroot().iter(tag="{urn:oasis:names:tc:xliff:document:1.2}trans-unit")
  for elem in root.iter(tag=ns+'trans-unit'):
    if elem.attrib.get('id') in to_delete:
      print '\t'+FAIL+'removing\t'+ENDC, elem.attrib.get('id')
      elem.getparent().remove(elem)

  # Add new trans-units
  for elem in root.iter(tag=ns+'body'): #skip over other elements between root and body
    body = elem

  # Create the new trans-unit elements
  for transunit in to_add:
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
  print '\n'+INFO+'### AutoXLIFF '+__version__+ENDC
  if (args.dry):
    print WARNING+'Dry run mode :'+ENDC+' No permanent change will be made\n'

  setup = get_setup(args)
  locfile = setup[0] # locfile points to a valid localization file path, either pre-existing or just created (empty)
  twigdir = setup[1]
  f = setup[2] # file descriptor of language file or None if file did not exist and needs to be created

  # Create XLIFF structure if file did not exist
  if f == None:
    xml_content = create_xliff(args)
  # If file exists, its content will be read instead
  else:
    xml_content = locfile

  # Load XLIFF either from existing file or empty structure as string
  root,ns = load_xliff(xml_content)

  if False == root:
    print FAIL+'FATAL : '+ENDC+' could not process XML content. Is this really XML/XLIFF ?'
    sys.exit(1)

  # Get existing trans-units from XLIFF object
  trans = get_trans_units(root,ns)

  # Explore Twig directory to build views list
  twigfiles = twig_explore(twigdir)

  # Parse Twig views to locate trans keywords
  keywords = parse_twig(twigfiles)

  # Update language file
  update_locfile(root,ns,trans,keywords,locfile,f,args)

# Execute
if __name__ == '__main__':
  Main()
