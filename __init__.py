# -*- coding: utf-8 -*-
# latin-1

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QUrl

from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.abetterpath.ui_options_abetterpath import Ui_ABetterPathOptionsPage
from picard.metadata import register_album_metadata_processor
from picard.metadata import register_track_metadata_processor
#from picard.script import register_script_function
from picard.album import Album
from picard.util import partial
from picard.mbxml import release_to_metadata

import pickle
import re, os, codecs, time
import unicodedata

#Create GUI Script
# http://www.riverbankcomputing.co.uk/software/pyqt/download
# C:\ProgramData\Python27\Lib\site-packages\PyQt4\pyuic4.bat BetterPath.ui > ui_options_betterpath.py

#Find multi-disc releases that need sorting out in the DB
# clear; echo; echo; find /mnt/media/Audio -type f -name 01.*\(1\)*; echo;
# clear; echo; echo; find /mnt/media/Audio -type f -name *\(1\)*; echo;
# find /mnt/media/Audio -type d -name *\(disc*
# find /mnt/media/Audio -type d -name *\(bonus*
# sudo find /mnt/media/Audio -type d -name *\(disc* -exec mv "{}" /mnt/media/Unsorted/Music/Multi-Disc \;
# sudo find /mnt/media/Audio -type d -name *\(bonus* -exec mv "{}" /mnt/media/Unsorted/Music/Multi-Disc \;

#Additional files to move
# folder.jpg fanart.jpg logo.png cdart.png

#Find empty folders
# find /mnt/media/Audio -type d -empty

#Find folder.png and folder.tiff
# find /mnt/media/Audio -name folder.png
# find /mnt/media/Audio -name folder.tiff

# http://tiptoes.hobby-site.com/mbz/lastfm/wordlists.html



PLUGIN_NAME = "A Better Path"
PLUGIN_AUTHOR = 'Mark Honeychurch'
PLUGIN_DESCRIPTION = 'Makes some extra tags to help with sorting out my music collection exactly how I like it!'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.16"]

def createCfgList():
 separator = '\x00'
 cfg = list()
 #cfg.append(("text", 'separator', '\x00'))
 #cfg.append(("text", 'various', "various artists"))
 cfg.append(("bool", 'artist_alpha', True))
 cfg.append(("text", 'artist_alpha_number', "#"))
 cfg.append(("text", 'artist_various', 'Various'))
 cfg.append(("bool", 'artist_sort_tag', True))
 cfg.append(("bool", 'artist_sort_itunes', True))
 cfg.append(("bool", 'artist_sort_itunes_albumartist', True))
 cfg.append(("bool", 'artist_sort_prefix', True))
 cfg.append(("bool", 'artist_sort_name', False))
 cfg.append(("bool", 'artist_sort_name_tag', False))
 cfg.append(("bool", 'album_sort_tag', True))
 cfg.append(("bool", 'album_date_folder', False))
 cfg.append(("bool", 'album_date_tag', True))
 cfg.append(("text", 'album_date_prefix', "["))
 cfg.append(("text", 'album_date_suffix', "] "))
 cfg.append(("text", 'album_date_format', "%Y"))
 cfg.append(("bool", 'album_release_folder', True))
 cfg.append(("text", 'album_release_prefix', " ("))
 cfg.append(("text", 'album_release_suffix', ")"))
 cfg.append(("bool", 'album_catalog_folder', False))
 cfg.append(("text", 'album_catalog_prefix', " ["))
 cfg.append(("text", 'album_catalog_suffix', "]"))
 cfg.append(("bool", 'album_sub_always', False))
 cfg.append(("bool", 'album_sub_folder', True))
 cfg.append(("bool", 'album_sub_tag', False))
 cfg.append(("text", 'album_sub_disc', "Disc "))
 cfg.append(("text", 'album_sub_prefix', " ("))
 cfg.append(("text", 'album_sub_suffix', ")"))
 cfg.append(("bool", 'album_sub_title_folder', True))
 cfg.append(("bool", 'album_sub_title_instead', False))
 cfg.append(("text", 'album_sub_title_separator', ": "))
 cfg.append(("bool", 'album_christmas', True))
 cfg.append(("int",  'album_compilation_threshold', 75))
 cfg.append(("text", 'album_foldersplit', "|"))
 cfg.append(("text", 'album_groups_separator', ": "))
 cfg.append(("bool", 'album_soundtrack_artist', False))
 cfg.append(("int",  'track_tracknumber_digits', 2))
 cfg.append(("text", 'track_tracknumber_separator', '. '))
 cfg.append(("bool", 'track_discnumber_filename', False))
 cfg.append(("bool", 'track_discnumber_single', False))
 cfg.append(("text", 'track_discnumber_separator', "-"))
 cfg.append(("bool", 'track_artist_filename', False))
 cfg.append(("bool", 'track_artist_compilation', True))
 cfg.append(("bool", 'track_artist_first', False))
 cfg.append(("text", 'track_artist_separator', " - "))
 cfg.append(("bool", 'track_tag_filename', True))
 cfg.append(("list", 'artist_sort_prefix_list',  pickle.dumps(('A', 'An', 'The'))))
 cfg.append(("list", 'album_date_formats', pickle.dumps(('%Y-%m-%d', '%Y-%m', '%Y'))))
 cfg.append(("dict", 'album_release_status_list', pickle.dumps({'bootleg': 'Bootleg', 'promotion': 'Promo'})))
 cfg.append(("list", 'album_release_type_compilation', pickle.dumps(('album', 'single', 'ep', 'live', 'other'))))
 cfg.append(("list", 'album_release_type_list', pickle.dumps(('Single', 'EP', 'Remix', 'Live'))))
 cfg.append(("list", 'album_compilation_excluded', pickle.dumps(('remix'))))
 cfg.append(("list", 'album_release_type_reverse', pickle.dumps((''))))
 cfg.append(("list", 'album_release_status_reverse', pickle.dumps(('Live'))))
 cfg.append(("list", 'album_catalog_order', pickle.dumps(('catalognumber', 'barcode', 'asin', 'date', 'totaltracks', 'releasetype'))))
 lists = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists')
 for infile in os.listdir(lists):
  if os.path.isfile(os.path.join(lists, infile)):
   nameSplit = infile.rsplit(".", 1)[0].split("-", 1)
   if len(nameSplit) > 1:
    cfg.append((nameSplit[0], nameSplit[1], readfile(lists, infile, nameSplit[0].lower())))
 return cfg


def splitPath(path):
 returnpath = list()
 split = path.replace("\\", "/").split("/")
 for sect in split:
  returnpath.append(sect.strip())
 return returnpath

def readfile(foldername, filename, fileType = "list", encoding = 'utf-8'):
 with codecs.open(os.path.join(foldername, filename), 'r', encoding) as f:
  line = f.readline()
  returnlist = list()
  returndict = dict()
  while line:
   if fileType == "list":
    returnlist.append(line.strip())
   else:
    split1 = line.split("=", 1)
    if len(split1) == 2:
     if fileType == "dict":
      returndict[split1[0].strip()] = split1[1].strip()
     elif fileType == "tuple":
      split2 = split1[0].split(",", 1)
      if len(split2) == 2:
       returndict[split1[1].strip()] = [split2[0].strip(), split2[1].strip()]
   line = f.readline()
  if fileType == "list":
   return pickle.dumps(returnlist)
  else:
   return pickle.dumps(returndict)
 f.closed

def replaceInvalidChars(dirpath, chars):
 filepathname = list()
 for dir in dirpath:
  for old, new in chars.iteritems():
   dir = dir.replace(old, new[0])
  if dir[0:3] == '...':
   dir = u'\u2026' + dir[3:]
  if dir[-3:] == '...':
   dir = dir[:-3] + u'\u2026'
  filepathname.append(dir.rstrip(". ").strip(" "))
 return filepathname

def getAlpha(text, folderName):
 if text:
  for initial in text:
   initial = unicodedata.normalize('NFKD', initial)[0:1]
   if initial.isalnum():
    if initial.isalpha():
     return initial.upper()
    if folderName:
     return folderName
    return initial
  if folderName:
   return folderName
  return text[0]

def swapPrefix(text, prefixes):
 for prefix in prefixes:
  if text.startswith(prefix + " "):
   return ", ".join((text[len(prefix):].strip(), prefix))
 return text

def isCompilation(release, albumartist, releasetype, various, album_compilation_excluded, album_compilation_threshold):
 if albumartist.lower() == various:
  return True
 if releasetype in album_compilation_excluded:
  return False
 trackCount = 0
 artistMatch = 0
 for track in release.medium_list[0].medium[0].track_list[0].track:
  trackCount += 1
#  if track.recording[0].artist_credit[0].name_credit[0].artist[0].name[0].text == albumartist:
#   artistMatch += 1
  for artist in track.recording[0].artist_credit[0].name_credit[0].artist:
   if artist.name[0].text == albumartist:
    artistMatch += 1
 if artistMatch / trackCount < (album_compilation_threshold / 100): #If less than 75% of the tracks have a credited artist that matches the Album Artist
  return True
 return False

def createAlbumSuffix(releasestatus, releasetype, album, config):
 suffixlist = list()
 album_release_status_list = pickle.loads(config['album_release_status_list'])
 for status in album_release_status_list:
  if releasestatus.lower() == status.lower():
   if not status.lower() in album.lower():
    suffixlist.append(album_release_status_list[status])
 for albumtype in pickle.loads(config['album_release_type_list']):
  if releasetype.lower() == albumtype.lower():
   if not albumtype.lower() in album.lower():
    suffixlist.append(albumtype)
 if len(suffixlist) > 1:
  if suffixlist[0] in pickle.loads(config['album_release_status_reverse']) or suffixlist[1] in pickle.loads(config['album_release_type_reverse']):
   suffixlist.reverse()
 if len(suffixlist) > 0:
  return config['album_release_prefix'] + ' '.join(suffixlist) + config['album_release_suffix']
 return ""

def getAlbumDate(dateList, album_date_formats):
 date = False
 for albumDate in dateList:
  for dateFormat in album_date_formats:
   try:
    dateTemp = datetime.strptime(albumDate, dateFormat)
   except:
    pass
   else:
    if not date:
     date = dateTemp
 return date

def checkArtistAliases(albumdetails, artist_album_to_artist, artists_to_artist, artist_to_artist, artist_to_artist_pseudonym):
 if albumdetails['name'] in artist_album_to_artist:
  if artist_album_to_artist[albumdetails['name']][0] == albumdetails['artist']:
   albumdetails['artist'] = artist_album_to_artist[albumdetails['name']][1]
 for realname in artists_to_artist:
  if albumdetails['artist'].startswith(realname):
   albumdetails['artist'] = realname
 if albumdetails['artist'] in artist_to_artist:
  albumdetails['artist'] = artist_to_artist[albumdetails['artist']]
 if albumdetails['artist'] in artist_to_artist_pseudonym:
  albumdetails['pseudonym'] = albumdetails['artist']
  albumdetails['artist'] = artist_to_artist_pseudonym[albumdetails['artist']]
 return albumdetails

def checkAlbumAliases(albumdetails, album_group_to_folder, separator = ": "):
 albumName = albumdetails['name']
 groups = list()
 for albumprefix, folder in album_group_to_folder.iteritems():
  if albumName.startswith(albumprefix) and albumprefix not in groups: # If our album name starts with one of our group prefixes, and the prefix hasn't already been
   albumdetails['path'] = splitPath(folder)
   groups.append(albumprefix)
   albumName = albumName[len(albumprefix):].lstrip(" :-,.") # Remove the album prefix and any joining characters
   if albumName[0:3] == 'by ':
    albumName = albumName[3:]
   if not albumName: # If there's nothing left to differentiate the album (which could cause clashes with multiple albums named the same)
    albumdetails['name'] = albumdetails['name'] + separator + albumdetails["artist"]
 albumdetails['path'].extend(groups)
 return albumdetails

def changePath(albumdetails, albumType, artist_album_to_folder, album_partial_to_folder, type_to_folder):
 for newPath, album in artist_album_to_folder.iteritems():
  if (album[0] == albumdetails['originalartist'] or album[0] == albumdetails['artist']) and (album[1] == albumdetails['originalname'] or album[1] == albumdetails['name']):
   return splitPath(newPath).append(albumdetails['artist'])
 for albumPart in album_partial_to_folder:
  if albumPart in albumdetails['originalname'] or albumPart in albumdetails['name']:
   return splitPath(album_partial_to_folder[albumPart]).append(albumdetails['artist'])
 if albumType.lower() in type_to_folder:
  return splitPath(type_to_folder[albumType.lower()]).append(albumdetails['artist'])
 return list()








def createAlbumTags(tagger, metadata, release, track = False):
 config = tagger.config.setting
 #albumdetails = {'name': metadata["album"], 'artist': metadata["albumartist"], 'originalname': metadata["album"], 'originalartist': metadata["albumartist"], 'pseudonym': '', 'type': '', 'group': list(), 'path': list()}
 #albumdetails = checkArtistAliases(checkAlbumAliases(albumdetails, pickle.loads(config['album_group_to_folder']), config['album_groups_separator']), pickle.loads(config['artist_album_to_artist']), pickle.loads(config['artists_to_artist']), pickle.loads(config['artist_to_artist']), pickle.loads(config['artist_to_artist_pseudonym']))
 #albumdetails['compilation'] = isCompilation(release, metadata["albumartist"], metadata["releasetype"], config['various'], config['album_compilation_excluded'], config['album_compilation_threshold'])
 albumdetails = checkArtistAliases(checkAlbumAliases({'name': metadata["album"], 'artist': metadata["albumartist"], 'originalname': metadata["album"], 'originalartist': metadata["albumartist"], 'pseudonym': '', 'type': '', 'path': list(), 'compilation': isCompilation(release, metadata["albumartist"], metadata["releasetype"], config['various'], config['album_compilation_excluded'], config['album_compilation_threshold'])}, pickle.loads(config['album_group_to_folder']), config['album_groups_separator']), pickle.loads(config['artist_album_to_artist']), pickle.loads(config['artists_to_artist']), pickle.loads(config['artist_to_artist']), pickle.loads(config['artist_to_artist_pseudonym']))
 if not albumdetails['path']:
  changePath(albumdetails, metadata['releasetype'], pickle.loads(config['artist_album_to_folder']), pickle.loads(config['album_partial_to_folder']), pickle.loads(config['type_to_folder']))
 if config['artist_sort_prefix']:
  albumdetails['artist'] = swapPrefix(albumdetails['artist'], config['artist_sort_prefix_list'])

 if albumdetails['path']:
  pass
 else:
  albumdetails['path'] = ["Music"]
  if albumdetails['compilation']:
   albumdetails['path'].append(config['artist_various'])
   if metadata["releasetype"].lower() in config['album_release_type_compilation']:
    albumdetails['path'].append('Compilation')
   else:
    albumdetails['path'].append(metadata["releasetype"].capitalize())
  else: #Album or Other or not set
   albumdetails['path'].append('Artists')
   if config['artist_alpha'] and albumdetails['artist']:
    albumdetails['path'].append(getAlpha(albumdetails['artist'], config['artist_alpha_number']))
   albumdetails['path'].append(albumdetails['artist'])
   if albumdetails['pseudonym']:
    if config['artist_sort_prefix']:
     albumdetails['pseudonym'] = swapPrefix(albumdetails['pseudonym'], pickle.loads(config['artist_sort_prefix_list']))
    albumdetails['path'].append(albumdetails['pseudonym'])
 albumDate = getAlbumDate((metadata["originaldate"], metadata["date"], metadata["album"].split(":")[0]), config['album_date_formats'])
 albumYear = ""
 if config['album_date_folder'] and albumDate:
  albumYear = config['album_date_prefix'] + time.strftime(config['album_date_format'], albumDate) + config['album_date_suffix']
 albumSuffix = createAlbumSuffix(metadata["releasestatus"], metadata["releasetype"], metadata["album"], config)
 albumdetails['path'].append(albumYear + albumdetails['name'] + albumSuffix)
 if not config['artist_sort_tag']:
  metadata["albumartistsort"] = albumdetails['artist']
 #metadata['filename'] = os.path.join(*filepathname)
 metadata['filename'] = '\x00'.join(albumdetails['path'])
 if albumdetails['compilation']:
  metadata['compilation'] = "1" # Mark the release as a compilation






def createTrackTags(tagger, metadata, release, track = False):
 config = tagger.config.setting
 trackdetails = dict()
 trackdetails['path'] = metadata['filename'].split('\x00')
 trackdetails['compilation'] = False
 if metadata["compilation"]:
  if int(metadata["compilation"]) == 1:
   trackdetails['compilation'] = True
 trackdetails['discs'] = 1
 trackdetails['discsuffix'] = ""
 if metadata["totaldiscs"]:
  trackdetails['discs'] = int(metadata["totaldiscs"])
  if trackdetails['discs'] > 1 or config['album_sub_always']:
   subDiscName = config['album_sub_disc'] + metadata["discnumber"]
   if metadata["discsubtitle"] and config['album_sub_title_folder']:
    if config['album_sub_title_instead']:
     subDiscName = metadata["discsubtitle"]
    else:
     subDiscName += config['album_sub_title_separator'] + metadata["discsubtitle"]
   if config['album_sub_folder']:
    trackdetails['path'].append(subDiscName)
   if config['album_sub_tag']:
    metadata["album"] += config['album_sub_prefix'] + subDiscName + config['album_sub_suffix']
 if metadata["tracknumber"]:
  tracknumber = metadata["tracknumber"].zfill(config['track_tracknumber_digits'])
  if config['track_discnumber_filename'] and (config['track_discnumber_single'] or trackdetails['discs'] > 1):
   tracknumber = metadata["discnumber"] + config['track_discnumber_separator'] + tracknumber
  trackdetails['filename'] = metadata["title"]
  if config['track_artist_filename'] or (config['track_artist_compilation'] and trackdetails['compilation']):
   if config['track_artist_first']:
    trackdetails['filename'] = metadata["artist"] + config['track_artist_separator'] + trackdetails['filename']
   else:
    trackdetails['filename'] = trackdetails['filename'] + config['track_artist_separator'] + metadata["artist"]
  for old, new in pickle.loads(config['chars_to_chars']).iteritems():
   trackdetails['filename'] = trackdetails['filename'].replace(old, new[0])
 trackdetails['path'] = replaceInvalidChars(trackdetails['path'], pickle.loads(config['chars_to_chars']))
 index = 0
 for namepart in reversed(trackdetails['path']):
  metadata['dir' + str(index)] = namepart
  index += 1
 metadata['name1'] = tracknumber
 metadata['name0'] = trackdetails['filename']
 trackdetails['path'].append(tracknumber + config['track_tracknumber_separator'] + trackdetails['filename'] + '.mp3')
 #metadata['filename'] = os.path.join(*trackdetails['path'])
 metadata['filename'] = "/".join(trackdetails['path'])
 if config['track_tag_filename']:
  metadata['~id3:TOFN'] = metadata['filename']
 if not config['artist_sort_tag']:
  metadata["artistsort"] = metadata["artist"]
 if not config['album_sort_tag']:
  metadata["albumsort"] = metadata["album"]
 if config['album_sub_tag'] and trackdetails['discsuffix']:
  metadata["albumsort"] += trackdetails['discsuffix']
 if config['artist_sort_itunes']:
  if config['artist_sort_itunes_albumartist']:
   metadata['~id3:TSO2'] = metadata['albumartistsort']
  else:
   metadata['~id3:TSO2'] = metadata['artistsort']







   

class abetterpathoptionspage(OptionsPage):
 NAME = "abetterpath"
 TITLE = "A Better Path"
 PARENT = "plugins"

 cfg = createCfgList()
 options = list()
 options.append(TextOption("setting", 'separator', '\x00'))
 options.append(TextOption("setting", 'various', "various artists"))
 for option in cfg:
  if option[0] == 'bool':
   options.append(BoolOption("setting", option[1], option[2]))
  elif option[0] == 'int':
   options.append(IntOption("setting", option[1], option[2]))
  else: # option[0] == 'text':
   options.append(TextOption("setting", option[1], option[2]))
  

 def __init__(self, parent=None):
  super(abetterpathoptionspage, self).__init__(parent)
  self.ui = Ui_ABetterPathOptionsPage()
  self.ui.setupUi(self)

 def load_defaults(self):
  pass

 def load(self):
  cfg = createCfgList()
  for option in cfg:
   if option[0] == 'bool':
    getattr(self.ui, option[1]).setChecked(self.config.setting[option[1]])
   elif option[0] == 'text':
    value = getattr(self.ui, option[1])
    value.setText(self.config.setting[option[1]])
   elif option[0] == 'int':
    value = getattr(self.ui, option[1])
    value.setInt(self.config.setting[option[1]])

def save(self):
 cfg = createCfgList()
 self.config.setting["artist_alpha"] = False
 self.config.setting["artist_alpha_number"] = "1"
 #self.config.setting["artist_alpha"] = self.ui.artist_alpha.isChecked
 #self.config.setting["artist_alpha_number"] = self.ui.artist_alpha.text
# for option in cfg:
#   if option[0] == 'bool':
#    value = getattr(self.ui, option[1])
#    self.config.setting[option[1]] = value.isChecked()
#   elif option[0] == 'text':
#    value = getattr(self.ui, option[1])
#    self.config.setting[option[1]] = value.text()
#   elif option[0] == 'int':
#    value = getattr(self.ui, option[1])
#    self.config.setting[option[1]] = value.value()
  #self.config.setting["artist_alpha"] = self.ui.artist_alpha()
  #self.config.setting["artist_alpha_number"] = self.ui.artist_alpha_number.text()



register_album_metadata_processor(createAlbumTags)
register_track_metadata_processor(createTrackTags)
register_options_page(abetterpathoptionspage)