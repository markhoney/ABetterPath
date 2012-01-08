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

#import pprint
#import pickle
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




PLUGIN_NAME = "A Better Path"
PLUGIN_AUTHOR = 'Mark Honeychurch'
PLUGIN_DESCRIPTION = 'Makes some extra tags to help with sorting out my music collection exactly how I like it!'
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.16"]


def defaultSettings():
 settings = dict()

 settings['folders'] = dict()
 settings['folders']['lists'] = dict()
 settings['folders']['lists']['base'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists')
 settings['folders']['lists']['artists'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists', 'artists')
 settings['folders']['lists']['albums'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists', 'albums')
 settings['folders']['lists']['albumgroups'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists', 'albums', 'groups')
 settings['folders']['lists']['test'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists', 'test')

 settings['chars'] = readfilelist(settings['folders']['lists']['base'], 'replacechars.txt')
 settings['various'] = "various artists"
 
 settings['artist'] = dict()
 settings['artist']['alpha'] = dict()
 settings['artist']['alpha']['folder'] = True
 settings['artist']['alpha']['number'] = "#"
 settings['artist']['various'] = dict()
 settings['artist']['various']['name'] = 'Various'
 settings['artist']['sort'] = dict()
 settings['artist']['sort']['tag'] = True
 settings['artist']['sort']['itunes'] = dict()
 settings['artist']['sort']['itunes']['tag'] = True
 settings['artist']['sort']['itunes']['albumartist'] = True
 settings['artist']['sort']['prefix'] = dict()
 settings['artist']['sort']['prefix']['folder'] = True
 settings['artist']['sort']['prefix']['list'] =  ('A', 'An', 'The')
 settings['artist']['sort']['name'] = dict()
 settings['artist']['sort']['name']['folder'] = False
 settings['artist']['sort']['name']['tag'] = False
 settings['artist']['lists'] = dict()
 settings['artist']['lists']['pseudonyms'] = readfilelist(settings['folders']['lists']['artists'], 'pseudonyms.txt')
 settings['artist']['lists']['aliases'] = readfilelist(settings['folders']['lists']['artists'], 'aliases.txt')
 settings['artist']['lists']['collaborations'] = readfilelist(settings['folders']['lists']['artists'], 'collaborations.txt')['list']
 settings['artist']['lists']['albums'] = readfilelist(settings['folders']['lists']['artists'], 'albums.txt')

 settings['album'] = dict()
 settings['album']['sort'] = dict()
 settings['album']['sort']['tag'] = True
 settings['album']['date'] = dict()
 settings['album']['date']['formats'] = ['%Y-%m-%d', '%Y-%m', '%Y']
 settings['album']['date']['folder'] = False
 settings['album']['date']['tag'] = True
 settings['album']['date']['prefix'] = "["
 settings['album']['date']['suffix'] = "] "
 settings['album']['date']['format'] = "%Y"
 settings['album']['release'] = dict()
 settings['album']['release']['folder'] = True
 settings['album']['release']['prefix'] = " ("
 settings['album']['release']['suffix'] = ")"
 settings['album']['release']['type'] = dict()
 settings['album']['release']['type']['compilation'] = ('album', 'single', 'ep', 'live', 'other')
 settings['album']['release']['type']['list'] = ('Single', 'EP', 'Remix', 'Live') # releasetype
 settings['album']['release']['type']['reverse'] = ('')
 settings['album']['release']['status'] = dict()
 settings['album']['release']['status']['list'] = {'bootleg': 'Bootleg', 'promotion': 'Promo'} # releasestatus
 settings['album']['release']['status']['reverse'] = ('Live')
 settings['album']['catalog'] = dict()
 settings['album']['catalog']['folder'] = False
 settings['album']['catalog']['prefix'] = " ["
 settings['album']['catalog']['suffix'] = "]"
 settings['album']['catalog']['order'] = ('catalognumber', 'barcode', 'asin', 'date', 'totaltracks', 'releasetype')
 settings['album']['sub'] = dict()
 settings['album']['sub']['always'] = False
 settings['album']['sub']['folder'] = True
 settings['album']['sub']['tag'] = False
 settings['album']['sub']['disc'] = "Disc "
 settings['album']['sub']['prefix'] = " ("
 settings['album']['sub']['suffix'] = ")"
 settings['album']['sub']['title'] = dict()
 settings['album']['sub']['title']['folder'] = True
 settings['album']['sub']['title']['instead'] = False
 settings['album']['sub']['title']['separator'] = ": "
 settings['album']['christmas'] = dict()
 settings['album']['christmas']['folder'] = True
 settings['album']['christmas']['name'] = 'Christmas'
 settings['album']['christmas']['foldersplit'] = "|"
 settings['album']['christmas']['location'] = settings['artist']['various']['name'] + settings['album']['christmas']['foldersplit'] + settings['album']['christmas']['name']
 settings['album']['christmas']['list'] = readfilelist(settings['folders']['lists']['albums'], 'christmas.txt')['list']
 settings['album']['compilation'] = dict()
 settings['album']['compilation']['excluded'] = ('remix')
 settings['album']['compilation']['threshold'] = 0.75
 settings['album']['lists'] = dict()
 settings['album']['lists']['spoken'] = readfilelist(settings['folders']['lists']['albums'], 'spokenword.txt')
 settings['album']['lists']['folderchange'] = readfilelist(settings['folders']['lists']['albums'], 'folderchange.txt')
 settings['album']['lists']['foldersplit'] = "|"
 settings['album']['lists']['groups'] = dict()
 settings['album']['lists']['groups']['separator'] = ": "
 settings['album']['lists']['groups']["mix"] = readfilelist(settings['folders']['lists']['albumgroups'], 'mixes.txt')['list']
 settings['album']['lists']['groups']["compilation"] = readfilelist(settings['folders']['lists']['albumgroups'], 'compilations.txt')['list']
 settings['album']["soundtrack"] = dict() 
 settings['album']["soundtrack"]['artist'] = False
 settings['album']["soundtrack"]['list'] = readfilelist(settings['folders']['lists']['albumgroups'], 'soundtracks.txt')['list']
 
 settings['track'] = dict()
 settings['track']['tracknumber'] = dict()
 settings['track']['tracknumber']['digits'] = 2
 settings['track']['tracknumber']['separator'] = '. '
 settings['track']['discnumber'] = dict()
 settings['track']['discnumber']['filename'] = False
 settings['track']['discnumber']['single'] = False
 settings['track']['discnumber']['separator'] = "-"
 settings['track']['artist'] = dict()
 settings['track']['artist']['filename'] = False
 settings['track']['artist']['compilation'] = True
 settings['track']['artist']['first'] = False
 settings['track']['artist']['separator'] = " - "
 settings['track']['tag'] = dict()
 settings['track']['tag']['filename'] = True
 
 return settings


#dontSortArtistNames = True

# $if2(%artist%,)
#$if($stricmp($left(%artist%,3),'The'),$right(%artist%,$sub($len(%artist%),4)),%artist%)

# http://tiptoes.hobby-site.com/mbz/lastfm/wordlists.html

# The File Naming string to use with this script is:





# $set(comment:description,%_recordingcomment%)
# $set(originaldate,%_originaldate%)
# metadata['originaldate'] = metadata['_originaldate']



def pprintToFile(foldername, filename, data, encoding = 'utf-8'):
 with codecs.open(os.path.join(foldername, filename), 'w', encoding) as f:
  pprint.pprint(data, f, 2, 9999)
 f.closed

def writefile(foldername, filename, data, encoding = 'utf-8'):
 with codecs.open(os.path.join(foldername, filename), 'w', encoding) as f:
  f.write(data)
 f.closed

def splitline(line):
 listsplit = line.split('=', 1)
 list = [listsplit[0]]
 if len(listsplit) == 2:
  list.extend(listsplit[1].split(',', 1))
 return ([x.strip() for x in list])

def readfilelist(foldername, filename, encoding = 'utf-8'):
 with codecs.open(os.path.join(foldername, filename), 'r', encoding) as f:
  line = f.readline()
  splittype = len(splitline(line))
  returndict = dict()
  if splittype == 1:
   returndict['list'] = list()
  while line:
   splitlist = splitline(line)
   if splittype == 1:
    returndict['list'].append(splitlist[0])
   elif splittype == 2:
    if splitlist[0] in returndict:
     returndict[splitlist[0]].append(splitlist[1])
    else:
     returndict[splitlist[0]] = [splitlist[1]]
   else:
    returndict[splitlist[2]] = [splitlist[1], splitlist[0]]
   line = f.readline()
  return returndict
 f.closed


# http://www.ascii-code.com/

# http://en.wikipedia.org/wiki/List_of_Unicode_characters#General_punctuation
# http://www.rishida.net/tools/conversion/


def replaceInvalidChars(dirpath):
 filepathname = list()
 for dir in dirpath:
  for old, new in settings['chars'].iteritems():
   dir = dir.replace(old, new[0])
  if dir[0:3] == '...':
   dir = u'\u2026' + dir[3:]
  if dir[-3:] == '...':
   dir = dir[:-3] + u'\u2026'
  filepathname.append(dir.rstrip(". ").strip(" "))
 return filepathname

def getalpha(text):
 if text:
  #return unidecode.unidecode(text)
  #text = unidecode.unidecode(text)
  for initial in text:
   initial = unicodedata.normalize('NFKD', initial)[0:1]
   if initial.isalnum():
    if initial.isalpha():
     return initial.upper()
    if settings['artist']['alpha']['number']:
     return settings['artist']['alpha']['number']
    return initial
  if settings['artist']['alpha']['number']:
   return settings['artist']['alpha']['number']
  return text[0]

def swapPrefix(text, prefixes):
 for prefix in prefixes:
  if text.startswith(prefix + " "):
   return ", ".join((text[len(prefix):].strip(), prefix))
 return text

def isCompilation(release, albumartist, releasetype):
 if albumartist.lower() == settings['various']:
  return True
 if releasetype in settings['album']['compilation']['excluded']:
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
 if artistMatch / trackCount < settings['album']['compilation']['threshold']: #If less than 75% of the tracks have a credited artist that matches the Album Artist
  return True

# If this is an EP, Single or Live release, add a bracketed suffix. This tests for:
#
#					|	official		bootleg					promomotional
#--------------------------------------------------------------------------------
#	album			|					Bootleg					Promo
#	other			|					Bootleg					Promo
#	compilation		|					Bootleg					Promo
#	single			|	Single			Bootleg Single			Promo Single
#	ep				|	EP				Bootleg EP				Promo EP
#	remix			|	Remix			Bootleg Remix			Promo Remix
#	live			|	Live			Live Bootleg			Live Promo

# Discarded option
#	compilation		|	Compilation		Bootleg Compilation		Promo Compilation

def createAlbumSuffix(releasestatus, releasetype, album):
 suffixlist = list()
 for status in settings['album']['release']['status']['list']:
  if releasestatus.lower() == status.lower():
   if not status.lower() in album.lower():
    suffixlist.append(settings['album']['release']['status']['list'][status])
 for albumtype in settings['album']['release']['type']['list']:
  if releasetype.lower() == albumtype.lower():
   if not albumtype.lower() in album.lower():
    suffixlist.append(albumtype)
 if len(suffixlist) > 1:
  if suffixlist[0] in settings['album']['release']['status']['reverse'] or suffixlist[1] in settings['album']['release']['type']['reverse']:
   suffixlist.reverse()
 if len(suffixlist) > 0:
  return settings['album']['release']['prefix'] + ' '.join(suffixlist) + settings['album']['release']['suffix']
 return ""

def getAlbumDate(dateList):
 date = False
 for albumDate in dateList:
  for dateFormat in settings['album']['date']['formats']:
   try:
    dateTemp = datetime.strptime(albumDate, dateFormat)
   except:
    pass
   else:
    if not date:
     date = dateTemp
 return date

def checkArtistAliases(albumdetails):
 if albumdetails['name'] in settings['artist']['lists']['albums']:
  if settings['artist']['lists']['albums'][albumdetails['name']][0] == albumdetails['artist']:
   albumdetails['artist'] = settings['artist']['lists']['albums'][albumdetails['name']][1]
 for realname in settings['artist']['lists']['collaborations']:
  if albumdetails['artist'].startswith(realname):
   albumdetails['artist'] = realname
 for realname in settings['artist']['lists']['aliases']:
  if albumdetails['artist'] in settings['artist']['lists']['aliases'][realname]:
   albumdetails['artist'] = realname
 for realname in settings['artist']['lists']['pseudonyms']:
  if albumdetails['artist'] in settings['artist']['lists']['pseudonyms'][realname]:
   albumdetails['pseudonym'] = albumdetails['artist']
   albumdetails['artist'] = realname
 return albumdetails

def checkAlbumAliases(albumdetails):
 albumName = albumdetails['name']
 for albumgroup in settings['album']['lists']['groups']:
  for albumprefix in settings['album']['lists']['groups'][albumgroup]:
   if albumName.startswith(albumprefix) and albumprefix not in albumdetails['group']: # If our album name starts with one of our gourp prefixes, and the prefix hasn't already been 
    albumdetails['type'] = albumgroup # Set the type of album (e.g. Mix, Compilation, etc)
    albumdetails['group'].append(albumprefix)
    albumName = albumName[len(albumprefix):].lstrip(" :-,.") # Remove the album prefix and any joining characters
    if albumName[0:3] == 'by ':
     albumName = albumName[3:]
    if not albumName: # If there's nothing left to differentiate the album (which could cause clashes with multiple albums named the same)
     albumdetails['name'] = albumdetails['name'] + settings['album']['lists']['groups']['separator'] + albumdetails["artist"]
 return albumdetails

def checkAliases(artistname, albumname):
 albumdetails = {'name': albumname, 'artist': artistname, 'pseudonym': '', 'type': '', 'group': list()}
 #newalbumdetails = albumdetails
 #newalbumdetails['name'] = ''
 #while albumdetails != newalbumdetails:
#  albumdetails = newalbumdetails
#  newalbumdetails = checkArtistAliases(checkAlbumAliases(albumdetails))
 albumdetails = checkArtistAliases(checkAlbumAliases(albumdetails))
 return albumdetails
 
def createAlbumTags(tagger, metadata, release, track = False):
 albumdetails = checkAliases(metadata["albumartist"], metadata["album"])
 albumdetails['compilation'] = False
 if isCompilation(release, metadata["albumartist"], metadata["releasetype"]):
  albumdetails['compilation'] = True

 albumdetails['path'] = list()
 if metadata['album'] in settings['album']['lists']['folderchange']:
  if settings['album']['lists']['folderchange'][metadata['album']][0] == metadata['albumartist']:
   albumdetails['path'] = settings['album']['lists']['folderchange'][metadata['album']][1].split(settings['album']['lists']['foldersplit'])
 if not albumdetails['path'] and settings['album']["soundtrack"]['artist'] and (metadata['releasetype'].lower() == 'soundtrack' or metadata['albumname'] in settings['album']["soundtrack"]["list"]):
  #albumdetails['path'] = list()
  albumdetails['path'].append(settings['artist']['various']['name'])
  albumdetails['path'].append('Soundtrack')
  for release in albumdetails['group']:
   albumdetails['path'].append(release)
 if settings['artist']['sort']['prefix']['folder']: 
  albumdetails['artist'] = swapPrefix(albumdetails['artist'], settings['artist']['sort']['prefix']['list'])
 if not albumdetails['path'] and settings['album']['christmas']['folder']:
  for listitem in settings['album']['christmas']['list']:
   if listitem in metadata['album']:
    albumdetails['path'] = settings['album']['christmas']['location'].split(settings['album']['christmas']['foldersplit'])
    albumdetails['path'].append(albumdetails['artist'])

 if albumdetails['path']:
  pass
 elif albumdetails["type"].lower() in settings['album']['lists']['spoken']:
  albumdetails['path'] = ["Spoken"]
  albumdetails['path'].append(settings['album']['lists']['spoken'][albumdetails["type"].lower()])
  albumdetails['path'].append(albumdetails['artist'])
 else:
  albumdetails['path'] = ["Music"]
  if albumdetails['artist'] == metadata["albumartist"] and (albumdetails['type'] or albumdetails['compilation']):
   albumdetails['path'].append(settings['artist']['various']['name'])
   if albumdetails["type"]:
    albumdetails['path'].append(albumdetails["type"].capitalize())
    for release in albumdetails['group']:
     albumdetails['path'].append(release)
   else:
    if metadata["releasetype"].lower() in settings['album']['release']['type']['compilation']:
     albumdetails['path'].append('Compilation')
    else:
     albumdetails['path'].append(metadata["releasetype"].capitalize())
  else: #Album or Other or not set
   albumdetails['path'].append('Artists')
   if settings['artist']['alpha']['folder'] and albumdetails['artist']:
    albumdetails['path'].append(getalpha(albumdetails['artist']))
   albumdetails['path'].append(albumdetails['artist'])
   if albumdetails['pseudonym']:
    if settings['artist']['sort']['prefix']['folder']:
     albumdetails['pseudonym'] = swapPrefix(albumdetails['pseudonym'], settings['artist']['sort']['prefix']['list'])
    albumdetails['path'].append(albumdetails['pseudonym'])

# Create an album year prefix for albums with a date set
# [1993] Siamese Dream
 albumDate = getAlbumDate((metadata["originaldate"], metadata["date"], metadata["album"].split(":")[0]))
 #if albumDate and settings['album']['date']['tag'] and not metadata['~id3:TDOR']:
 # metadata['~id3:TDOR'] = time.strftime('%Y-%m-%d', albumDate)
 albumYear = ""
 if settings['album']['date']['folder'] and albumDate:
  albumYear = settings['album']['date']['prefix'] + time.strftime(settings['album']['date']['format'], albumDate) + settings['album']['date']['suffix']

 albumSuffix = createAlbumSuffix(metadata["releasestatus"], metadata["releasetype"], metadata["album"])

#Build our album directory
 albumdetails['path'].append(albumYear + albumdetails['name'] + albumSuffix)

 if not settings['artist']['sort']['tag']:
  metadata["albumartistsort"] = albumdetails['artist']

 #metadata['filename'] = os.path.join(*filepathname)
 metadata['filename'] = '\x00'.join(albumdetails['path'])
 if albumdetails['compilation']:
  metadata['compilation'] = "1" # Mark the release as a compilation

def createTrackTags(tagger, metadata, release, track = False):
 trackdetails = dict()
 trackdetails['path'] = metadata['filename'].split('\x00')
 trackdetails['compilation'] = False
 if metadata["compilation"]:
  if int(metadata["compilation"]) == 1:
   trackdetails['compilation'] = True
 #metadata["compilation"] = ""

# Add an album sub-folder if this is a bonus or multi-part album, e.g.
# xx/Bonus Disc
# Greatest Hits; Rotten Apples/Judas Ø
# Live in Washington D.C./Disc 1
# Mellon Collie and the Infinite Sadness/Dawn to Dusk
# if metadata["discnumber"] or discbonus:
 trackdetails['discs'] = 1
 trackdetails['discsuffix'] = ""
 if metadata["totaldiscs"]:
  trackdetails['discs'] = int(metadata["totaldiscs"])
  if trackdetails['discs'] > 1 or settings['album']['sub']['always']:
   subDiscName = settings['album']['sub']['disc'] + metadata["discnumber"]
   if metadata["discsubtitle"] and settings['album']['sub']['title']['folder']:
    if settings['album']['sub']['title']['instead']:
     subDiscName = metadata["discsubtitle"]
    else:
     subDiscName += settings['album']['sub']['title']['separator'] + metadata["discsubtitle"]
   if settings['album']['sub']['folder']:
    trackdetails['path'].append(subDiscName)
   if settings['album']['sub']['tag']:
    metadata["album"] += settings['album']['sub']['prefix'] + subDiscName + settings['album']['sub']['suffix']

 if metadata["tracknumber"]:
  tracknumber = metadata["tracknumber"].zfill(settings['track']['tracknumber']['digits'])
  if settings['track']['discnumber']['filename'] and (settings['track']['discnumber']['single'] or trackdetails['discs'] > 1):
   tracknumber = metadata["discnumber"] + settings['track']['discnumber']['separator'] + tracknumber
  trackdetails['filename'] = metadata["title"]
  if settings['track']['artist']['filename'] or (settings['track']['artist']['compilation'] and trackdetails['compilation']):
   if settings['track']['artist']['first']:
    trackdetails['filename'] = metadata["artist"] + settings['track']['artist']['separator'] + trackdetails['filename']
   else:
    trackdetails['filename'] = trackdetails['filename'] + settings['track']['artist']['separator'] + metadata["artist"]
  for old, new in settings['chars'].iteritems():
   trackdetails['filename'] = trackdetails['filename'].replace(old, new[0])

 trackdetails['path'] = replaceInvalidChars(trackdetails['path'])

 #filepathname.reverse()
 index = 0
 for namepart in reversed(trackdetails['path']):
  metadata['dir' + str(index)] = namepart
  index += 1
 metadata['name1'] = tracknumber
 metadata['name0'] = trackdetails['filename']

 #filepathname.reverse()
 trackdetails['path'].append(tracknumber + settings['track']['tracknumber']['separator'] + trackdetails['filename'] + '.mp3')
 #metadata['filename'] = os.path.join(*trackdetails['path'])
 metadata['filename'] = "/".join(trackdetails['path'])
 if settings['track']['tag']['filename']:
  metadata['~id3:TOFN'] = metadata['filename']
 
 if not settings['artist']['sort']['tag']:
  metadata["artistsort"] = metadata["artist"]

 if not settings['album']['sort']['tag']:
  metadata["albumsort"] = metadata["album"]
 if settings['album']['sub']['tag'] and trackdetails['discsuffix']:
  metadata["albumsort"] += trackdetails['discsuffix']

 if settings['artist']['sort']['itunes']['tag']:
  if settings['artist']['sort']['itunes']['albumartist']:
   metadata['~id3:TSO2'] = metadata['albumartistsort']
  else:
   metadata['~id3:TSO2'] = metadata['artistsort']



class abetterpathoptionspage(OptionsPage):
 NAME = "betterpath"
 TITLE = "BetterPath"
 PARENT = "plugins"
 
 options = [
			BoolOption("setting", "betterpath_alphaFolder", True),
			TextOption("setting", "betterpath_alphaNumber", "#")
		   ]


 def __init__(self, parent=None):
  super(abetterpathoptionspage, self).__init__(parent)
  self.ui = Ui_ABetterPathOptionsPage()
  self.ui.setupUi(self)


 def load(self):
  configArray = ["betterpath_alphaFolder", "betterpath_alphaNumber"]
  cfg = self.config.setting
  for var in configArray:
   setattr(self.ui, var, cfg[var])

 def save(self):
  configArray = ["betterpath_alphaFolder", "betterpath_alphaNumber"]
  for var in configArray:
   self.config.setting[var] = getattr(self.ui, var)


settings = defaultSettings()

#register_album_metadata_processor(compilationCheck)
register_album_metadata_processor(createAlbumTags)
register_track_metadata_processor(createTrackTags)

register_options_page(abetterpathoptionspage)