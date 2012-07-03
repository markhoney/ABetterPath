# -*- coding: utf-8 -*-
# latin-1

from PyQt4 import QtCore #, QtGui
#from PyQt4.QtCore import QUrl

from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.abetterpath.ui_options_abetterpath import Ui_ABetterPathOptionsPage
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
#from picard.script import register_script_function
from picard.album import Album
from picard.util import partial
from picard.mbxml import release_to_metadata

#import traceback
import re, os, codecs, time, sys
import unicodedata

PLUGIN_NAME = "A Better Path"
PLUGIN_AUTHOR = 'Mark Honeychurch'
PLUGIN_DESCRIPTION = 'Makes some extra tags to help with sorting out my music collection exactly how I like it!'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.16"]

class addalbum():
 def __init__(self, tagger, metadata, release):
  self.name = ""
  self.config = cfg()
  self.cfg = self.config.createcfg(tagger.config.setting)
  #self.tagger = tagger
  self.metadata = metadata
  self.release = release
  self.albumdetails = {'name': metadata["album"], 'artist': metadata["albumartist"], 'originalname': metadata["album"], 'originalartist': metadata["albumartist"], 'pseudonym': '', 'type': '', 'path': list(), 'compilation': self._compilation(release, metadata["albumartist"], metadata["releasetype"])}
  self._albumAliases()
  self._artistAliases()
  if not self.albumdetails['path']:
   self.albumdetails['path'] = self._changePath(metadata['releasetype'])
  if self.cfg['artist_sort_prefix']:
   self.albumdetails['artist'] = self._swapPrefix(self.albumdetails['artist'], self.cfg['artist_sort_prefix_list'])
  if not self.albumdetails['path']:
   self.albumdetails['path'] = ["Music"]
   if self.albumdetails['compilation']:
    self.albumdetails['path'].append(self.cfg['artist_various'])
    if metadata["releasetype"].lower() in self.cfg['album_release_type_compilation']:
     self.albumdetails['path'].append('Compilation')
    else:
     self.albumdetails['path'].append(metadata["releasetype"].capitalize())
   else: #Album or Other or not set
    self.albumdetails['path'].append('Artists')
    if self.cfg['artist_alpha'] and self.albumdetails['artist']:
     self.albumdetails['path'].append(self._alpha())
    self.albumdetails['path'].append(self.albumdetails['artist'])
    if self.albumdetails['pseudonym']:
     if self.cfg['artist_sort_prefix']:
      self.albumdetails['pseudonym'] = self._swapPrefix(self.albumdetails['pseudonym'], self.cfg['artist_sort_prefix_list'])
     self.albumdetails['path'].append(self.albumdetails['pseudonym'])
  albumDate = self._date((metadata["originaldate"], metadata["date"], metadata["album"].split(":")[0]))
  albumYear = ""
  if self.cfg['album_date_folder'] and albumDate:
   albumYear = self.cfg['album_date_prefix'] + time.strftime(self.cfg['album_date_format'], albumDate) + self.cfg['album_date_suffix']
  albumSuffix = self._suffix(metadata["releasestatus"], metadata["releasetype"], metadata["album"])
  self.albumdetails['path'].append(albumYear + self.albumdetails['name'] + albumSuffix)
  if not self.cfg['artist_sort_tag']:
   metadata["albumartistsort"] = self.albumdetails['artist']
  #metadata['filename'] = self.cfg['separator'].join(self.albumdetails['path'])
  metadata['~filename'] = '\x00'.join(self.albumdetails['path'])
  if self.albumdetails['compilation']:
   metadata['compilation'] = "1" # Mark the release as a compilation

 def _date(self, dateList):
  date = False
  for albumDate in dateList:
   for dateFormat in self.cfg['album_date_formats']:
    try:
     dateTemp = datetime.strptime(albumDate, dateFormat)
    except:
     pass
    else:
     if not date:
      date = dateTemp
  return date

 def _artistAliases(self):
  if self.albumdetails['name'] in self.cfg['artist_album_to_artist']:
   if self.cfg['artist_album_to_artist'][self.albumdetails['name']][0] == self.albumdetails['artist']:
    self.albumdetails['artist'] = self.cfg['artist_album_to_artist'][self.albumdetails['name']][1]
  for realname in self.cfg['artists_to_artist']:
   if self.albumdetails['artist'].startswith(realname):
    self.albumdetails['artist'] = realname
  if self.albumdetails['artist'] in self.cfg['artist_to_artist']:
   self.albumdetails['artist'] = self.cfg['artist_to_artist'][self.albumdetails['artist']]
  if self.albumdetails['artist'] in self.cfg['artist_to_artist_pseudonym']:
   self.albumdetails['pseudonym'] = self.albumdetails['artist']
   self.albumdetails['artist'] = self.cfg['artist_to_artist_pseudonym'][self.albumdetails['artist']]

 def _albumAliases(self):
  albumName = self.albumdetails['name']
  groups = list()
  for albumprefix, folder in self.cfg['album_group_to_folder'].iteritems():
   if albumName.startswith(albumprefix) and albumprefix not in groups: # If our album name starts with one of our group prefixes, and the prefix hasn't already been
    self.albumdetails['path'] = self._splitPath(folder)
    groups.append(albumprefix)
    albumName = albumName[len(albumprefix):].lstrip(" :-,.") # Remove the album prefix and any joining characters
    if albumName[0:3] == 'by ':
     albumName = albumName[3:]
    if not albumName: # If there's nothing left to differentiate the album (which could cause clashes with multiple albums named the same)
     self.albumdetails['name'] = self.albumdetails['name'] + self.cfg['album_groups_separator'] + self.albumdetails["artist"]
  self.albumdetails['path'].extend(groups)

 def _changePath(self, albumType):
  for newPath, album in self.cfg['artist_album_to_folder'].iteritems():
   if (album[0] == self.albumdetails['originalartist'] or album[0] == self.albumdetails['artist']) and (album[1] == self.albumdetails['originalname'] or album[1] == self.albumdetails['name']):
    albumPath = self._splitPath(newPath)
    albumPath.append(self.albumdetails['artist'])
    return albumPath
    #return self._splitPath(newPath).append(self.albumdetails['artist'])
  for albumPart in self.cfg['album_partial_to_folder']:
   if albumPart in self.albumdetails['originalname'] or albumPart in self.albumdetails['name']:
    albumPath = self._splitPath(self.cfg['album_partial_to_folder'][albumPart])
    albumPath.append(self.albumdetails['artist'])
    return albumPath
    #return self._splitPath(album_partial_to_folder[albumPart]).append(self.albumdetails['artist'])
  if albumType.lower() in self.cfg['type_to_folder']:
   albumPath = self._splitPath(self.cfg['type_to_folder'][albumType.lower()])
   albumPath.append(self.albumdetails['artist'])
   return albumPath
   #return self._splitPath(type_to_folder[albumType.lower()]).append(self.albumdetails['artist'])
  return list()

 def _compilation(self, release, albumartist, releasetype):
  if albumartist.lower() == self.cfg['various']:
   return True
  if releasetype in self.cfg['album_compilation_excluded']:
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
  if artistMatch / trackCount < (self.cfg['album_compilation_threshold'] / 100): #If less than 75% of the tracks have a credited artist that matches the Album Artist
   return True
  return False

 def _swapPrefix(self, text, prefixes):
  for prefix in prefixes:
   if text.startswith(prefix + " "):
    return ", ".join((text[len(prefix):].strip(), prefix))
  return text

 def _suffix(self, releasestatus, releasetype, album):
  suffixlist = list()
  album_release_status_list = self.cfg['album_release_status_list']
  for status in album_release_status_list:
   if releasestatus.lower() == status.lower():
    if not status.lower() in album.lower():
     suffixlist.append(album_release_status_list[status])
  for albumtype in self.cfg['album_release_type_list']:
   if releasetype.lower() == albumtype.lower():
    if not albumtype.lower() in album.lower():
     suffixlist.append(albumtype)
  if len(suffixlist) > 1:
   if suffixlist[0] in self.cfg['album_release_status_reverse'] or suffixlist[1] in self.cfg['album_release_type_reverse']:
    suffixlist.reverse()
  if len(suffixlist) > 0:
   return self.cfg['album_release_prefix'] + ' '.join(suffixlist) + self.cfg['album_release_suffix']
  return ""

 def _splitPath(self, path):
  returnpath = list()
  for sect in path.replace("\\", "/").split("/"):
   returnpath.append(sect.strip())
  return returnpath

 def _alpha(self): # self.albumdetails['artist'], self.cfg['artist_alpha_number']
  if self.albumdetails['artist']:
   for initial in self.albumdetails['artist']:
    initial = unicodedata.normalize('NFKD', initial)[0:1]
    if initial.isalnum():
     if initial.isalpha():
      return initial.upper()
     if self.cfg['artist_alpha_number']:
      return self.cfg['artist_alpha_number']
     return initial
   if self.cfg['artist_alpha_number']:
    return self.cfg['artist_alpha_number']
   return self.albumdetails['artist'][0]

 def _genres():
  from pylast import pylast
  lastfm = pylast.LastFMNetwork(api_key = "9407ca2b8eaa65632a283563ddd56792", api_secret = "2b5494bbe88d9f3cb473e2981e325be8", username = "", password_hash = "")
  try:
   artistinfo = lastfm.get_artist_by_mbid(self.metadata['musicbrainz_albumartistid'])
   albuminfo = lastfm.get_album_by_mbid(self.metadata['musicbrainz_albumid'])
  except:
   pass
  else:
   try:
    possibleGenres = artistinfo.get_top_tags(limit = 10)
   except:
    pass
   else:
    genre = "" 
    for genres in possibleGenres:
     genreName = genres.item.name.title()
     if (genreName in matchGenres):
      if (genre == ""):
       genre = genreName
    if (genre == ""):
     try:
      genre = possibleGenres[0].item.name.title()
     except:
      pass
    artistGenres[track["artist"]] = genre
  if (track["artist"] in artistGenres):
   track["genre"] = artistGenres[track["artist"]]
 
# metadata["mood"]
# metadata["genre"]
# metadata['~id3:WOAR'] # Artist Webpage
# metadata['~id3:TCMP'] # iTunes Compilation
# metadata['~id3:USLT'] # Unsynced Lyrics
# metadata['~id3:TIT3'] # Subtitle




class addtrack():
 def __init__(self, tagger, metadata, release, track):
  self.config = cfg()
  self.cfg = self.config.createcfg(tagger.config.setting)
  self.trackdetails = dict()
  #self.trackdetails['path'] = metadata['filename'].split(config['separator'])
  self.trackdetails['path'] = metadata['~filename'].split('\x00')
  self.trackdetails['compilation'] = False
  if metadata["compilation"]:
   if int(metadata["compilation"]) == 1:
    self.trackdetails['compilation'] = True
  self.trackdetails['discs'] = 1
  self.trackdetails['discsuffix'] = ""
  if metadata["totaldiscs"]:
   self.trackdetails['discs'] = int(metadata["totaldiscs"])
   if self.trackdetails['discs'] > 1 or self.cfg['album_sub_always']:
    subDiscName = self.cfg['album_sub_disc'] + metadata["discnumber"]
    if metadata["discsubtitle"] and self.cfg['album_sub_title_folder']:
     if self.cfg['album_sub_title_instead']:
      subDiscName = metadata["discsubtitle"]
     else:
      subDiscName += self.cfg['album_sub_title_separator'] + metadata["discsubtitle"]
    if self.cfg['album_sub_folder']:
     self.trackdetails['path'].append(subDiscName)
    if self.cfg['album_sub_tag']:
     metadata["album"] += self.cfg['album_sub_prefix'] + subDiscName + self.cfg['album_sub_suffix']
  if metadata["tracknumber"]:
   tracknumber = metadata["tracknumber"].zfill(self.cfg['track_tracknumber_digits'])
   if self.cfg['track_discnumber_filename'] and (self.cfg['track_discnumber_single'] or self.trackdetails['discs'] > 1):
    tracknumber = metadata["discnumber"] + self.cfg['track_discnumber_separator'] + tracknumber
   self.trackdetails['filename'] = metadata["title"]
   if self.cfg['track_artist_filename'] or (self.cfg['track_artist_compilation'] and self.trackdetails['compilation']):
    if self.cfg['track_artist_first']:
     self.trackdetails['filename'] = metadata["artist"] + self.cfg['track_artist_separator'] + self.trackdetails['filename']
    else:
     self.trackdetails['filename'] = self.trackdetails['filename'] + self.cfg['track_artist_separator'] + metadata["artist"]
   for old, new in self.cfg['chars_to_chars'].iteritems():
    self.trackdetails['filename'] = self.trackdetails['filename'].replace(old[0], new[0])
    #sys.stderr.write(old + "\n")
  self.trackdetails['path'] = self._replaceChars(self.trackdetails['path'])
  index = 0
  for namepart in reversed(self.trackdetails['path']):
   metadata['~dir' + str(index)] = namepart
   index += 1
  metadata['~name1'] = tracknumber
  metadata['~name0'] = self.trackdetails['filename']
  self.trackdetails['path'].append(tracknumber + self.cfg['track_tracknumber_separator'] + self.trackdetails['filename'] + '.mp3')
  #metadata['filename'] = os.path.join(*self.trackdetails['path'])
  metadata['~filename'] = "/".join(self.trackdetails['path'])
  if self.cfg['track_tag_filename']:
   metadata['~id3:TOFN'] = metadata['~filename']
  if not self.cfg['artist_sort_tag']:
   metadata["artistsort"] = metadata["artist"]
  if not self.cfg['album_sort_tag']:
   metadata["albumsort"] = metadata["album"]
  if self.cfg['album_sub_tag'] and self.trackdetails['discsuffix']:
   metadata["albumsort"] += self.trackdetails['discsuffix']
  if self.cfg['artist_sort_itunes']:
   if self.cfg['artist_sort_itunes_albumartist']:
    metadata['~id3:TSO2'] = metadata['albumartistsort']
   else:
    metadata['~id3:TSO2'] = metadata['artistsort']

 def _replaceChars(self, dirpath):
  filepathname = list()
  for dir in dirpath:
   for old, new in self.cfg['chars_to_chars'].iteritems():
    dir = dir.replace(old[0], new[0])
   if dir[0:3] == '...':
    dir = u'\u2026' + dir[3:]
   if dir[-3:] == '...':
    dir = dir[:-3] + u'\u2026'
   filepathname.append(dir.rstrip(". ").strip(" "))
  return filepathname






class cfg():
 def __init__(self):
  self.config = list()
  self.config.append(("str", 'separator', '\x00'))
  self.config.append(("str", 'various', "various artists"))
  self.config.append(("bool", 'artist_alpha', True, "Alpha Folder", "Create an alphabetical folder level for the first letter of an artist's name"))
  self.config.append(("str", 'artist_alpha_number', "#", "Number Symbol"))
  self.config.append(("bool", 'artist_alpha_upper', True, "Convert "))
  self.config.append(("bool", 'artist_alpha_unicode_convert', True, "Convert", ""))
  self.config.append(("bool", 'artist_alpha_nonalpha_ignore', False, "Ignore"))
  self.config.append(("str", 'artist_various', 'Various'))
  self.config.append(("bool", 'artist_sort_tag', True))
  self.config.append(("bool", 'artist_sort_itunes', True))
  self.config.append(("bool", 'artist_sort_itunes_albumartist', True))
  self.config.append(("bool", 'artist_sort_prefix', True))
  self.config.append(("bool", 'artist_sort_name', False))
  self.config.append(("bool", 'artist_sort_name_tag', False))
  self.config.append(("bool", 'album_sort_tag', True))
  self.config.append(("bool", 'album_date_folder', False))
  self.config.append(("bool", 'album_date_tag', True))
  self.config.append(("str", 'album_date_prefix', "["))
  self.config.append(("str", 'album_date_suffix', "] "))
  self.config.append(("str", 'album_date_format', "%Y"))
  self.config.append(("bool", 'album_release_folder', True))
  self.config.append(("str", 'album_release_prefix', " ("))
  self.config.append(("str", 'album_release_suffix', ")"))
  self.config.append(("bool", 'album_catalog_folder', False))
  self.config.append(("str", 'album_catalog_prefix', " ["))
  self.config.append(("str", 'album_catalog_suffix', "]"))
  self.config.append(("bool", 'album_sub_always', False))
  self.config.append(("bool", 'album_sub_folder', True))
  self.config.append(("bool", 'album_sub_tag', False))
  self.config.append(("str", 'album_sub_disc', "Disc "))
  self.config.append(("str", 'album_sub_prefix', " ("))
  self.config.append(("str", 'album_sub_suffix', ")"))
  self.config.append(("bool", 'album_sub_title_folder', True))
  self.config.append(("bool", 'album_sub_title_instead', False))
  self.config.append(("str", 'album_sub_title_separator', ": "))
  self.config.append(("bool", 'album_christmas', True))
  self.config.append(("int",  'album_compilation_threshold', 75))
  self.config.append(("str", 'album_foldersplit', "|"))
  self.config.append(("str", 'album_groups_separator', ": "))
  self.config.append(("bool", 'album_soundtrack_artist', False))
  self.config.append(("int",  'track_tracknumber_digits', 2))
  self.config.append(("str", 'track_tracknumber_separator', '. '))
  self.config.append(("bool", 'track_discnumber_filename', False))
  self.config.append(("bool", 'track_discnumber_single', False))
  self.config.append(("str", 'track_discnumber_separator', "-"))
  self.config.append(("bool", 'track_artist_filename', False))
  self.config.append(("bool", 'track_artist_compilation', True))
  self.config.append(("bool", 'track_artist_first', False))
  self.config.append(("str", 'track_artist_separator', " - "))
  self.config.append(("bool", 'track_tag_filename', True))
  self.config.append(("list", 'artist_sort_prefix_list',  self.writeList(['A', 'An', 'The'])))
  self.config.append(("list", 'album_date_formats', self.writeList(['%Y-%m-%d', '%Y-%m', '%Y'])))
  self.config.append(("dict", 'album_release_status_list', self.writeList({'bootleg': 'Bootleg', 'promotion': 'Promo'})))
  self.config.append(("list", 'album_release_type_compilation', self.writeList(['album', 'single', 'ep', 'live', 'other'])))
  self.config.append(("list", 'album_release_type_list', self.writeList(['Single', 'EP', 'Remix', 'Live'])))
  self.config.append(("list", 'album_compilation_excluded', self.writeList(['remix'])))
  self.config.append(("list", 'album_release_type_reverse', self.writeList([''])))
  self.config.append(("list", 'album_release_status_reverse', self.writeList(['Live'])))
  self.config.append(("list", 'album_catalog_order', self.writeList(['catalognumber', 'barcode', 'asin', 'date', 'totaltracks', 'releasetype'])))
  lists = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists')
  for infile in os.listdir(lists):
   if os.path.isfile(os.path.join(lists, infile)):
    nameSplit = infile.rsplit(".", 1)[0].split("-", 1)
    if len(nameSplit) > 1:
#     fileContents = ""
#     if fileDefaults:
     fileContents = self._readfile(lists, infile, nameSplit[0].lower())
     self.config.append((nameSplit[0], nameSplit[1], fileContents))

 def createcfg(self, setting):
  self.cfg = dict()
  for option in self.config:
   try:
    self.cfg[option[1]] = self.readList(setting[option[1]])
   except:
    self.cfg[option[1]] = self.readList(option[2], option[0])
  return self.cfg

 def _readfile(self, foldername, filename, fileType = "list", encoding = 'utf-8'):
  with codecs.open(os.path.join(foldername, filename), 'r', encoding) as f:
   return f.read()
  f.closed

 def readList(self, inlist, fileType = "list"):
  if fileType in ['bool', 'str', 'int']:
   return inlist
  returnlist = list()
  returndict = dict()
  if fileType == "list":
   for line in inlist.splitlines():
    if line.strip()[0] != "#":
     returnlist.append(line.strip())
   return returnlist
  elif fileType == "dict":
   for line in inlist.splitlines():
    split1 = line.split("=", 1)
    if len(split1) == 2:
     returndict[split1[0].strip()] = split1[1].strip()
  elif fileType == "tuple":
   for line in inlist.splitlines():
    split1 = line.split("=", 1)
    if len(split1) == 2:
     split2 = split1[0].split(",", 1)
     if len(split2) == 2:
      returndict[split1[1].strip()] = [split2[0].strip(), split2[1].strip()]
  return returndict

 def writeList(self, inlist):
  fileType = type(inlist).__name__
  if fileType in ['bool', 'str', 'int']:
   return inlist
  elif fileType == "list":
   return "\n".join(inlist)
  else: # fileType == "dict":
   returnstring = ""
   if type(inlist.itervalues().next()).__name__ == "str":
    for key, value in inlist.iteritems():
     returnstring += key + " = " + value
   else: # fileType == "tuple":
    for key, value in inlist.iteritems():
     returnstring += value[0] + ", " + value[1] + " = " + key
   return returnstring
  





class abetterpathoptionspage(OptionsPage):
 NAME = "abetterpath"
 TITLE = "A Better Path"
 PARENT = "plugins"

 def __init__(self, parent = None):
  super(abetterpathoptionspage, self).__init__(parent)
  self.ui = Ui_ABetterPathOptionsPage()
  self.ui.setupUi(self)
  self.loadVars = {'bool': 'setChecked', 'int': 'setValue', 'str': 'setText', 'list': 'setText', 'dict': 'setText', 'tuple': 'setText'}
  self.saveVars = {'bool': 'isChecked', 'int': 'value', 'str': 'text', 'list': 'text', 'dict': 'text', 'tuple': 'text'}
  self.cfg = cfg()
  self.separator = ","
  self.options = list()
  for option in self.cfg.config:
   if option[0] == 'bool':
    self.options.append(BoolOption("setting", option[1], option[2]))
   elif option[0] == 'int':
    self.options.append(IntOption("setting", option[1], option[2]))
   else: # option[0] == 'int':
    self.options.append(TextOption("setting", option[1], option[2]))

 def load_defaults(self):
  for option in self.cfg.config:
   try:
    getattr(getattr(self.ui, option[1]), self.loadVars[option[0]])(option[2]) # self.ui.alpha_number.setChecked(option[2])
   except:
    pass # If there's no control in the UI, don't try to set it!

 def save_defaults(self):
  for option in self.cfg.config:
   self.config.setting[option[1]] = option[2]

 def load(self):
  for option in self.cfg.config:
   try:
    getattr(getattr(self.ui, option[1]), self.loadVars[option[0]])(self.config.setting[option[1]]) # self.ui.alpha_number.setChecked(self.config.setting['alpha_number'])
   except:
    pass # If there's no control in the UI, don't try to set it!

 def save(self):
  for option in self.cfg.config:
   try:
    self.config.setting[option[1]] = getattr(getattr(self.ui, option[1]), self.saveVars[option[0]])() # self.config.setting['alpha_number'] = self.ui.alpha_number.isChecked()
   except:
    self.config.setting[option[1]] = option[2]  # self.config.setting['alpha_number'] = option[2]


register_album_metadata_processor(addalbum)
register_track_metadata_processor(addtrack)
register_options_page(abetterpathoptionspage)