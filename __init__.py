# -*- coding: utf-8 -*-
# latin-1

# EchoNest
# Your API Key: A0ODEL28DRISOEJ0D 
# Your Consumer Key: 1a40f64d5331f0cca495645c743c0674 
# Your Shared Secret: A4y/h2lASQGe7/jTzKMS4Q
# "http://developer.echonest.com/api/v4/artist/urls?format=xml&api_key=A0ODEL28DRISOEJ0D&id=musicbrainz:artist:" +

# Rovio (AllMusic)
# Key: 3qjjbgkjms3nc9jcnr2xt5r8
# Shared Secret: dbA8sN4bJV
# http://developer.rovicorp.com/siggen
# http://api.rovicorp.com/data/v1/descriptor/musicgenres?include=all&format=xml&apikey=3qjjbgkjms3nc9jcnr2xt5r8&sig=

from PyQt4 import QtCore #, QtGui
#from PyQt4.QtCore import QUrl

from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.abetterpath.ui_options_abetterpath import Ui_ABetterPathOptionsPage
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
#from picard.script import register_script_function
from picard.album import Album
from picard.webservice import REQUEST_DELAY
from picard.util import partial
from picard.mbxml import release_to_metadata

import re, os, codecs, time, sys
import unicodedata
from datetime import datetime, timedelta

PLUGIN_NAME = "A Better Path"
PLUGIN_AUTHOR = 'Mark Honeychurch'
PLUGIN_DESCRIPTION = 'Makes some extra tags to help with sorting out my music collection exactly how I like it!'
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["1.0"]

class addalbum():
 def __init__(self, album, metadata, release):
  self.config = cfg()
  self.config.load(album.config.setting)
  self.cfg = self.config.cfg
  from picard.webservice import REQUEST_DELAY
  REQUEST_DELAY[(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'])] = 200
  self.album = album
  self.metadata = metadata
  self.release = release
  #sys.stderr.write("album: " + pprint.pformat(self.album) + "\n\n")
  #sys.stderr.write("metadata: " + pprint.pformat(self.metadata) + "\n\n")
  #sys.stderr.write("release: " + pprint.pformat(self.release) + "\n\n")
  self.albumartist = self.metadata["albumartist"]
  self.artistpseudonym = ""
  self.albumname = self.metadata["album"]
  self.metadata['compilation'] = self._compilation()
  self.path = list()
  self.tags = dict()
  self.urls = dict()
  firstartist = self.metadata['musicbrainz_albumartistid'].split(';')[0]
  self.urls['lastfm_mbidalbum_toptags'] = "/2.0/?method=album.gettoptags&mbid=" + self.metadata['musicbrainz_albumid'] + "&api_key=9407ca2b8eaa65632a283563ddd56792"
  self.urls['lastfm_album_toptags'] = "/2.0/?method=album.gettoptags&artist=" + self._lastfmencode(self.albumartist) + "&album=" + self._lastfmencode(self.albumname) + "&api_key=9407ca2b8eaa65632a283563ddd56792"
  self.urls['lastfm_mbidartist_toptags'] = "/2.0/?method=artist.gettoptags&mbid=" + firstartist + "&api_key=9407ca2b8eaa65632a283563ddd56792"
  self.urls['lastfm_artist_toptags'] = "/2.0/?method=artist.gettoptags&artist=" + self._lastfmencode(self.albumartist) + "&api_key=9407ca2b8eaa65632a283563ddd56792"
  self.urls['echonest_artist_tags'] = "/api/v4/artist/terms?api_key=A0ODEL28DRISOEJ0D&id=musicbrainz:artist:" + self._lastfmencode(firstartist) + "&format=xml"
  self.urls['echonest_artist_url'] = "/api/v4/artist/urls?api_key=A0ODEL28DRISOEJ0D&id=musicbrainz:artist:" + self._lastfmencode(firstartist) + "&format=xml"
  self._albumAliases()
  self._artistAliases()
  self._changePath()
  if self.cfg['abetterpath_artist_sort_prefix']:
   self.albumartist = self._swapPrefix(self.albumartist, self.cfg['abetterpath_artist_sort_prefix_list'])
  if not self.path:
   self.path = ["Music"]
   if self.metadata['compilation'] == "1":
    self.path.append(self.cfg['abetterpath_artist_various'])
    if self.metadata["releasetype"].lower() in self.cfg['abetterpath_album_release_type_compilation']:
     self.path.append('Compilation')
    else:
     self.path.append(self.metadata["releasetype"].capitalize())
   else: #Album or Other or not set
    self.path.append('Artists')
    if self.cfg['abetterpath_artist_alpha'] and self.albumartist:
     self.path.append(self._alpha())
    self.path.append(self.albumartist)
    if self.artistpseudonym:
     if self.cfg['abetterpath_artist_sort_prefix']:
      self.artistpseudonym = self._swapPrefix(self.artistpseudonym, self.cfg['abetterpath_artist_sort_prefix_list'])
     self.path.append(self.artistpseudonym)
  albumDate = self._date()
  albumYear = ""
  if self.cfg['abetterpath_album_date_folder'] and albumDate:
   albumYear = self.cfg['abetterpath_album_date_prefix'] + time.strftime(self.cfg['abetterpath_album_date_format'], albumDate) + self.cfg['abetterpath_album_date_suffix']
  albumSuffix = self._suffix()
  self.path.append(albumYear + self.albumname + albumSuffix)
  if not self.cfg['abetterpath_artist_sort_tag']:
   self.metadata["albumartistsort"] = self.albumartist
  self._albumtags()
  #self._artisturl()
  self.metadata['~filename'] = self.cfg['abetterpath_tag_separator'].join(self.path)
  self._folderdate()

 def _lastfmencode(self, string):
  #return QtCore.QUrl.toPercentEncoding(string)
  #return QtCore.QUrl.toPercentEncoding(unicode(QtCore.QUrl.toPercentEncoding(string)))
  #return QtCore.QUrl.toPercentEncoding(unicodedata.normalize('NFKD', string)) # .encode('ascii', 'ignore')
  output = ""
  for letter in string:
   output += unicodedata.normalize('NFKD', letter)[0]
  return QtCore.QUrl.toPercentEncoding(output)

 def _albumAliases(self):
  albumName = self.albumname
  groups = list()
  for albumprefix, folder in self.cfg['abetterpath_album_group_to_folder'].iteritems():
   if albumName.startswith(albumprefix) and albumprefix not in groups: # If our album name starts with one of our group prefixes, and the prefix hasn't already been
    self.path = self._splitPath(folder)
    groups.append(albumprefix)
    albumName = albumName[len(albumprefix):].lstrip(" :-,.") # Remove the album prefix and any joining characters
    if albumName[0:3] == 'by ':
     albumName = albumName[3:]
    if not albumName: # If there's nothing left to differentiate the album (which could cause clashes with multiple albums named the same)
     self.albumname = self.albumname + self.cfg['abetterpath_album_groups_separator'] + self.albumartist
  self.path.extend(groups)

 def _artistAliases(self):
  if (self.albumartist, self.albumname) in self.cfg['abetterpath_artist_album_to_artist']:
   self.albumartist = self.cfg['abetterpath_artist_album_to_artist'][(self.albumartist, self.albumname)]
  for realname in self.cfg['abetterpath_artist_to_artistprefix']:
   if self.albumartist.startswith(realname):
    self.albumartist = realname
  if self.albumartist in self.cfg['abetterpath_artist_to_artist']:
   self.albumartist = self.cfg['abetterpath_artist_to_artist'][self.albumartist]
  if self.albumartist in self.cfg['abetterpath_artist_to_artist_pseudonym']:
   self.artistpseudonym = self.albumartist
   self.albumartist = self.cfg['abetterpath_artist_to_artist_pseudonym'][self.albumartist]

 def _changePath(self):
  if (self.albumartist, self.albumname) in self.cfg['abetterpath_artist_album_to_folder']:
   self.path = self._splitPath(self.cfg['abetterpath_artist_album_to_folder'][(self.albumartist, self.albumname)])
   self.path.append(self.albumartist)
   return
  #for albumPart in self.cfg['abetterpath_album_partial_to_folder']:
  # if albumPart in self.metadata['album'] or albumPart in self.albumname:
  #  self.path = self._splitPath(self.cfg['abetterpath_album_partial_to_folder'][albumPart])
  #  self.path.append(self.albumartist)
  #  return
  if self.metadata['releasetype'].lower() in self.cfg['abetterpath_album_type_to_folder']:
   self.path = self._splitPath(self.cfg['abetterpath_album_type_to_folder'][self.metadata['releasetype'].lower()])
   self.path.append(self.albumartist)

 def _compilation(self):
  if self.metadata["albumartist"].lower() == self.cfg['abetterpath_tag_various']: # self.cfg['va_name']
   return "1"
  if self.metadata["releasetype"] in self.cfg['abetterpath_album_compilation_excluded']:
   return "0"
  trackCount = 0
  artistMatch = 0
  for track in self.release.medium_list[0].medium[0].track_list[0].track:
   trackCount += 1
 #  if track.recording[0].artist_credit[0].name_credit[0].artist[0].name[0].text == self.metadata["albumartist"]:
 #   artistMatch += 1
   for artist in track.recording[0].artist_credit[0].name_credit[0].artist:
    if artist.name[0].text == self.metadata["albumartist"]:
     artistMatch += 1
  if artistMatch / trackCount < (self.cfg['abetterpath_album_compilation_threshold'] / 100): #If less than 75% of the tracks have a credited artist that matches the Album Artist
   return "1"
  return "0"

 def _swapPrefix(self, text, prefixes):
  for prefix in prefixes:
   if text.startswith(prefix + " "):
    return ", ".join((text[len(prefix):].strip(), prefix))
  return text

 def _suffix(self):
  # 'abetterpath_album_release_status_list', {'bootleg': 'Bootleg', 'promotion': 'Promo'}
  # 'abetterpath_album_release_type_compilation', ['album', 'single', 'ep', 'live', 'other']
  # 'abetterpath_album_release_type_list', ['Single', 'EP', 'Remix', 'Live']
  # 'abetterpath_album_compilation_excluded', ['remix']
  # 'abetterpath_album_release_type_reverse', ['Live']
  # 'abetterpath_album_release_status_reverse', ['']
  # 'abetterpath_album_catalog_order', ['catalognumber', 'barcode', 'asin', 'date', 'totaltracks', 'releasetype']
  suffixlist = list()
  for status in self.cfg['abetterpath_album_release_status_list']:
   if self.metadata["releasestatus"].lower() == status.lower():
    if not status.lower() in self.metadata["album"].lower():
     suffixlist.append(self.cfg['abetterpath_album_release_status_list'][status])
  for albumtype in self.cfg['abetterpath_album_release_type_list']:
   if self.metadata["releasetype"].lower() == albumtype.lower():
    if not albumtype.lower() in self.metadata["album"].lower():
     suffixlist.append(albumtype)
  if len(suffixlist) > 1:
   if suffixlist[0] in self.cfg['abetterpath_album_release_status_reverse'] or suffixlist[1] in self.cfg['abetterpath_album_release_type_reverse']:
    suffixlist.reverse()
  if len(suffixlist) > 0:
   return self.cfg['abetterpath_album_release_prefix'] + ' '.join(suffixlist) + self.cfg['abetterpath_album_release_suffix']
  return ""

 def _splitPath(self, path):
  returnpath = list()
  for sect in path.replace("\\", "/").split("/"):
   returnpath.append(sect.strip())
  return returnpath

 def _alpha(self): # self.albumartist, self.cfg['abetterpath_artist_alpha_number']
  if self.albumartist:
   for initial in self.albumartist:
    initial = unicodedata.normalize('NFKD', initial)[0:1]
    if initial.isalnum():
     if initial.isalpha():
      return initial.upper()
     if self.cfg['abetterpath_artist_alpha_number']:
      return self.cfg['abetterpath_artist_alpha_number']
     return initial
   if self.cfg['abetterpath_artist_alpha_number']:
    return self.cfg['abetterpath_artist_alpha_number']
   return self.albumartist[0]

 def _lyrics(self):
  # metadata['~id3:USLT'] # Unsynced Lyrics
  pass
 
 def _albumtags(self):
  self._lastfmmbidalbumtags()

 def _lastfmmbidalbumtags(self):
  self.album._requests += 1
  #sys.stderr.write("http://" + self.cfg['abetterpath_http_lastfm_host'] + ":" + str(self.cfg['abetterpath_http_lastfm_port']) + self.urls['lastfm_mbidalbum_toptags'] + "\n")
  self.album.tagger.xmlws.get(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'], self.urls['lastfm_mbidalbum_toptags'], partial(self._processlastfmmbidalbumtags))

 def _processlastfmmbidalbumtags(self, data, http, error):
  try:
   self._lastfmtags(data.lfm[0].toptags[0].tag)
  except:
   self._lastfmalbumtags()
  else:
   self._lastfmartisttags()

 def _lastfmalbumtags(self):
  self.album._requests += 1
  #sys.stderr.write("http://" + self.cfg['abetterpath_http_lastfm_host'] + ":" + str(self.cfg['abetterpath_http_lastfm_port']) + self.urls['lastfm_album_toptags'] + "\n")
  self.album.tagger.xmlws.get(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'], self.urls['lastfm_album_toptags'], partial(self._processlastfmalbumtags))

 def _processlastfmalbumtags(self, data, http, error):
  try:
   self._lastfmtags(data.lfm[0].toptags[0].tag)
  except:
   pass
  self._lastfmmbidartisttags()

 def _lastfmmbidartisttags(self):
  if self.metadata["albumartist"] <> "Various Artists":
   self.album._requests += 1
   #sys.stderr.write("http://" + self.cfg['abetterpath_http_lastfm_host'] + ":" + str(self.cfg['abetterpath_http_lastfm_port']) + self.urls['lastfm_mbidartist_toptags'] + "\n")
   self.album.tagger.xmlws.get(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'], self.urls['lastfm_mbidartist_toptags'], partial(self._processlastfmmbidartisttags))
  else:
   self._processtags()

 def _processlastfmmbidartisttags(self, data, http, error):
  try:
   self._lastfmtags(data.lfm[0].toptags[0].tag)
  except:
   self._lastfmartisttags()
  else:
   self._processtags()
  #self._echonestartisttags()
  
 def _lastfmartisttags(self):
  if self.metadata["albumartist"] <> "Various Artists":
   self.album._requests += 1
   #sys.stderr.write("http://" + self.cfg['abetterpath_http_lastfm_host'] + ":" + str(self.cfg['abetterpath_http_lastfm_port']) + self.urls['lastfm_artist_toptags'] + "\n")
   self.album.tagger.xmlws.get(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'], self.urls['lastfm_artist_toptags'], partial(self._processlastfmartisttags))
  else:
   self._processtags()

 def _processlastfmartisttags(self, data, http, error):
  try:
   self._lastfmtags(data.lfm[0].toptags[0].tag)
  except:
   pass
  #self._echonestartisttags()
  self._processtags()

 def _echonestartisttags(self, data, http, error):
  if self.metadata["albumartist"] <> "Various Artists":
   self.album._requests += 1
   #sys.stderr.write("http://" + self.cfg['abetterpath_http_echonest_host'] + ":" + str(self.cfg['abetterpath_http_echonest_port']) + self.urls['echonest_artist_tags'] + "\n")
   self.album.tagger.xmlws.get(self.cfg['abetterpath_http_echonest_host'], self.cfg['abetterpath_http_echonest_port'], self.urls['echonest_artist_tags'], partial(self._processechonestartisttags))
  else:
   self._processtags()

 def _processechonestartisttags(self, data, http, error):
  for tag in data.response[0].terms:
   try:
    self._addtag(tag.name[0].text.title(), int(float(tag.weight[0].text) * 100))
   except:
    pass
  self._processtags()
  
 def _processtags(self):
  if self.tags:
   for tag in self.tags.copy():
    #sys.stderr.write(tag.encode('ascii', 'ignore') + " = " + str(self.tags[tag]) + "\n")
    if tag in self.cfg['abetterpath_tag_to_tag']:
     self.tags[self.cfg['abetterpath_tag_to_tag'][tag]] = self.tags[tag]
     del self.tags[tag]
   self._filtergenres()
   self._filtertags(self.cfg['abetterpath_tag_moods'], self.cfg['abetterpath_album_mood_max'], self.cfg['abetterpath_album_mood_threshold'], "mood")
  self.album._requests = 0
  self.album._finalize_loading(None)

 def _lastfmtags(self, tags):
  try:
   for tag in tags:
    self._addtag(tag.name[0].text.title(), int(tag.count[0].text))
  except:
   pass

 def _addtag(self, tag, score):
  if tag in self.tags:
   self.tags[tag] += score
  else:
   self.tags[tag] = score

 def _filtergenres(self):
  genre = dict()
  subgenres = list()
  for tag in sorted(self.tags, key = self.tags.get, reverse = True):
   if tag in self.cfg['abetterpath_tag_genres']: # (tagname.title() for tagname in )
    if self.cfg['abetterpath_tag_genres'][tag] in genre:
     genre[self.cfg['abetterpath_tag_genres'][tag]] += self.tags[tag]
    else:
     genre[self.cfg['abetterpath_tag_genres'][tag]] = self.tags[tag]
    if len(subgenres) < self.cfg['abetterpath_album_genre_max'] and self.tags[tag] >= self.cfg['abetterpath_album_genre_threshold'] and self.cfg['abetterpath_tag_genres'][tag] <> tag:
     subgenres.append(tag)
  if genre:
   self.metadata['grouping'] = max(genre, key=genre.get)
  if subgenres:
   #self.metadata['genre'] = self.cfg['abetterpath_tag_separator'].join(subgenres)
   self.metadata['genre'] = subgenres
  
 def _filtertags(self, whitelist, maxvalues, threshold, tagname):
  filtered = list()
  for tag in sorted(self.tags, key = self.tags.get, reverse = True):
   if len(filtered) < maxvalues and self.tags[tag] >= threshold and tag in whitelist:
    filtered.append(tag)
  if filtered:
   #self.metadata[tagname] = self.cfg['abetterpath_tag_separator'].join(filtered)
   self.metadata[tagname] = filtered

 def _artisturl(self):
  """
  Get artist URLs from EchoNest
  """
  if self.metadata["albumartist"] <> "Various Artists":
   self.album._requests += 1
   #sys.stderr.write(self.cfg['abetterpath_http_echonest_host'] + ":" + self.cfg['abetterpath_http_echonest_port'] + self.urls['echonest_artist_url'] + "\n")
   self.album.tagger.xmlws.get(self.cfg['abetterpath_http_echonest_host'], self.cfg['abetterpath_http_echonest_port'], self.urls['echonest_artist_url'], partial(self._processurls))

 def _processurls(self, data, http, error):
  for url in ["aolmusic_url", "amazon_url", "itunes_url", "lastfm_url", "mb_url", "myspace_url", "wikipedia_url"]:
   try:
    #sys.stderr.write(getattr(data.response[0].urls[0].urls[0], url)[0].text + "\n")
    if getattr(data.response[0].urls[0].urls[0], url)[0].text <> "None":
     self.metadata['~id3:WOAR'] = getattr(data.response[0].urls[0].urls[0], url)[0].text
   except:
    pass
  self.album._requests -= 1
  self.album._finalize_loading(None)

 def _folderdate(self):
  """
  Recursively Make the folder that the files are going to be moved to, and change the date of the folder to match the original release date of the release
  """
  try:
   timeInt = int(time.mktime(self._date().timetuple()))
  except:
   pass
  else:
   timeTuple = (timeInt, timeInt)
   folderPath = os.path.join(self.album.config.setting["move_files_to"], *replaceChars(self.path, self.cfg['abetterpath_tag_chars_to_chars']))
   #if self.album.config.setting["move_files"] and not os.path.exists(folderPath):
   # os.makedirs(folderPath)
   try:
    os.utime(folderPath, timeTuple)
   except:
    pass
   #sys.stderr.write(folderPath + "\n")

 def _date(self):
  date = list()
  albumtitledate = ""
  if len(self.metadata["album"].split(":")) == 2:
   albumtitledate = self.metadata["album"].split(":")[0]
  for albumDate in [self.metadata["originaldate"], self.metadata["date"], albumtitledate]:
   for dateFormat in self.cfg['abetterpath_album_date_formats']:
    try:
     return datetime.strptime(albumDate, dateFormat)
    except:
     pass






class addtrack():
 def __init__(self, album, metadata, release, track):
  self.config = cfg()
  self.config.load(album.config.setting)
  self.cfg = self.config.cfg
  self.album = album
  self.metadata = metadata
  self.release = release
  self.track = track
  self.path = self.metadata['~filename'].split(self.cfg['abetterpath_tag_separator'])
  self.tracknumber = 0
  self.trackname = self.metadata["title"]
  #import pprint
  #sys.stderr.write("album: " + pprint.pformat(self.album) + "\n\n")
  #sys.stderr.write("metadata: " + pprint.pformat(self.metadata) + "\n\n")
  #sys.stderr.write("release: " + pprint.pformat(self.release) + "\n\n")
  #sys.stderr.write("track: " + pprint.pformat(self.track) + "\n\n")
  self.urls = dict()
  self.urls['lastfm_track'] = "/2.0/?method=track.gettoptags&mbid=" + self.metadata['musicbrainz_trackid'] + "&api_key=9407ca2b8eaa65632a283563ddd56792"
  if int(self.metadata['totaldiscs']) > 1 or self.cfg['abetterpath_album_sub_always']:
   subDiscName = self.cfg['abetterpath_album_sub_disc'] + self.metadata["discnumber"]
   if self.metadata["discsubtitle"] and self.cfg['abetterpath_album_sub_title_folder']:
    if self.cfg['abetterpath_album_sub_title_instead']:
     subDiscName = self.metadata["discsubtitle"]
    else:
     subDiscName += self.cfg['abetterpath_album_sub_title_separator'] + self.metadata["discsubtitle"]
   if self.cfg['abetterpath_album_sub_folder']:
    self.path.append(subDiscName)
   if self.cfg['abetterpath_album_sub_tag']:
    self.metadata["album"] += self.cfg['abetterpath_album_sub_prefix'] + subDiscName + self.cfg['abetterpath_album_sub_suffix']
  if self.metadata["tracknumber"]:
   self.tracknumber = self.metadata["tracknumber"].zfill(self.cfg['abetterpath_track_tracknumber_digits'])
   if self.cfg['abetterpath_track_discnumber_filename'] and (self.cfg['abetterpath_track_discnumber_single'] or self.metadata['totaldiscs'] > 1):
    self.tracknumber = self.metadata["discnumber"] + self.cfg['abetterpath_track_discnumber_separator'] + self.tracknumber
   if self.cfg['abetterpath_track_artist_filename'] or (self.cfg['abetterpath_track_artist_compilation'] and self.metadata['compilation'] == "1"):
    if self.cfg['abetterpath_track_artist_first']:
     self.trackname = self.metadata["artist"] + self.cfg['abetterpath_track_artist_separator'] + self.trackname
    else:
     self.trackname = self.trackname + self.cfg['abetterpath_track_artist_separator'] + self.metadata["artist"]
   for old, new in self.cfg['abetterpath_tag_chars_to_chars'].iteritems():
    self.trackname = self.trackname.replace(old[0], new[0])
  self.path = replaceChars(self.path, self.cfg['abetterpath_tag_chars_to_chars'])
  index = 0
  for namepart in reversed(self.path):
   self.metadata['~dir' + str(index)] = namepart
   index += 1
  self.metadata['~name1'] = self.tracknumber
  self.metadata['~name0'] = self.trackname
  self.path.append(self.tracknumber + self.cfg['abetterpath_track_tracknumber_separator'] + self.trackname + '.' + 'mp3') # self.metadata['~extension']
  #self._tracktags()
  if self.cfg['abetterpath_track_tag_filename']:
   self.metadata['~id3:TOFN'] = "/".join(self.path)
  if not self.cfg['abetterpath_artist_sort_tag']:
   self.metadata["artistsort"] = self.metadata["artist"]
  if not self.cfg['abetterpath_album_sort_tag']:
   self.metadata["albumsort"] = self.metadata["album"]
  if self.cfg['abetterpath_artist_sort_itunes']:
   if self.cfg['abetterpath_artist_sort_itunes_albumartist']:
    self.metadata['~id3:TSO2'] = self.metadata['albumartistsort']
   else:
    self.metadata['~id3:TSO2'] = self.metadata['artistsort']

 def _tracktags(self):
  self.album._requests += 1
  #sys.stderr.write("http://" + self.cfg['abetterpath_http_lastfm_host'] + ":" + str(self.cfg['abetterpath_http_lastfm_port']) + self.urls['lastfm_track'] + "\n")
  self.album.tagger.xmlws.get(self.cfg['abetterpath_http_lastfm_host'], self.cfg['abetterpath_http_lastfm_port'], self.urls['lastfm_track'], partial(self._moods))

 def _moods(self, data, http, error):
  tags = list()
  try:
   for fmtag in data.lfm[0].toptags[0].tag:
    tags.append(fmtag.name[0].text.title())
  except:
   pass
  if tags:
   moods = list()
   for tag in tags:
    if tag in self.cfg['abetterpath_tag_moods']:
     moods.append(tag)
  if moods:
   self.metadata["mood"] = self.cfg['abetterpath_tag_separator'].join(moods)
  self.album._requests -= 1
  self.album._finalize_loading(None)


def replaceChars(dirpath, chars):
 filepathname = list()
 for dir in dirpath:
  for old, new in chars.iteritems():
   dir = dir.replace(old[0], new[0])
  if dir[0:3] == '...':
   dir = u'\u2026' + dir[3:]
  if dir[-3:] == '...':
   dir = dir[:-3] + u'\u2026'
  filepathname.append(dir.rstrip(". ").strip(" "))
 return filepathname



class cfg():
 def __init__(self):
  self.defaults = list()
  self.defaults.append(("str",  'abetterpath_tag_separator', '\x00'))
  self.defaults.append(("str",  'abetterpath_http_lastfm_host', "ws.audioscrobbler.com"))
  self.defaults.append(("int",  'abetterpath_http_lastfm_port', 80))
  self.defaults.append(("str",  'abetterpath_http_echonest_host', "developer.echonest.com"))
  self.defaults.append(("int",  'abetterpath_http_echonest_port', 80))
  self.defaults.append(("str",  'abetterpath_tag_various', "various artists"))
  self.defaults.append(("bool", 'abetterpath_artist_alpha', True, "Alpha Folder", "Create an alphabetical folder level for the first letter of an artist's name"))
  self.defaults.append(("str",  'abetterpath_artist_alpha_number', "#", "Number Symbol"))
  self.defaults.append(("bool", 'abetterpath_artist_alpha_upper', True, "Convert "))
  self.defaults.append(("bool", 'abetterpath_artist_alpha_unicode_convert', True, "Convert", ""))
  self.defaults.append(("bool", 'abetterpath_artist_alpha_nonalpha_ignore', False, "Ignore"))
  self.defaults.append(("bool", 'abetterpath_artist_alpha_nonalpha_ignore', False, "Ignore"))
  self.defaults.append(("str",  'abetterpath_artist_various', 'Various'))
  self.defaults.append(("bool", 'abetterpath_artist_sort_tag', True))
  self.defaults.append(("bool", 'abetterpath_artist_sort_itunes', True))
  self.defaults.append(("bool", 'abetterpath_artist_sort_itunes_albumartist', True))
  self.defaults.append(("bool", 'abetterpath_artist_sort_prefix', True))
  self.defaults.append(("bool", 'abetterpath_artist_sort_name', False))
  self.defaults.append(("bool", 'abetterpath_artist_sort_name_tag', False))
  self.defaults.append(("bool", 'abetterpath_album_sort_tag', True))
  self.defaults.append(("bool", 'abetterpath_album_date_folder', False))
  self.defaults.append(("bool", 'abetterpath_album_date_tag', True))
  self.defaults.append(("str",  'abetterpath_album_date_prefix', "["))
  self.defaults.append(("str",  'abetterpath_album_date_suffix', "] "))
  self.defaults.append(("str",  'abetterpath_album_date_format', "%Y"))
  self.defaults.append(("bool", 'abetterpath_album_release_folder', True))
  self.defaults.append(("str",  'abetterpath_album_release_prefix', " ("))
  self.defaults.append(("str",  'abetterpath_album_release_suffix', ")"))
  self.defaults.append(("bool", 'abetterpath_album_catalog_folder', False))
  self.defaults.append(("str",  'abetterpath_album_catalog_prefix', " ["))
  self.defaults.append(("str",  'abetterpath_album_catalog_suffix', "]"))
  self.defaults.append(("bool", 'abetterpath_album_sub_always', False))
  self.defaults.append(("bool", 'abetterpath_album_sub_folder', True))
  self.defaults.append(("bool", 'abetterpath_album_sub_tag', False))
  self.defaults.append(("str",  'abetterpath_album_sub_disc', "Disc "))
  self.defaults.append(("str",  'abetterpath_album_sub_prefix', " ("))
  self.defaults.append(("str",  'abetterpath_album_sub_suffix', ")"))
  self.defaults.append(("bool", 'abetterpath_album_sub_title_folder', True))
  self.defaults.append(("bool", 'abetterpath_album_sub_title_instead', False))
  self.defaults.append(("str",  'abetterpath_album_sub_title_separator', ": "))
  self.defaults.append(("bool", 'abetterpath_album_christmas', True))
  self.defaults.append(("int",  'abetterpath_album_compilation_threshold', 75))
  self.defaults.append(("str",  'abetterpath_album_foldersplit', "|"))
  self.defaults.append(("str",  'abetterpath_album_groups_separator', ": "))
  self.defaults.append(("bool", 'abetterpath_album_soundtrack_artist', False))
  self.defaults.append(("int",  'abetterpath_album_genre_threshold', 1))
  self.defaults.append(("int",  'abetterpath_album_genre_max', 5))
  self.defaults.append(("int",  'abetterpath_album_mood_threshold', 0))
  self.defaults.append(("int",  'abetterpath_album_mood_max', 5))
  self.defaults.append(("int",  'abetterpath_track_tracknumber_digits', 2))
  self.defaults.append(("str",  'abetterpath_track_tracknumber_separator', '. '))
  self.defaults.append(("bool", 'abetterpath_track_discnumber_filename', False))
  self.defaults.append(("bool", 'abetterpath_track_discnumber_single', False))
  self.defaults.append(("str",  'abetterpath_track_discnumber_separator', "-"))
  self.defaults.append(("bool", 'abetterpath_track_artist_filename', False))
  self.defaults.append(("bool", 'abetterpath_track_artist_compilation', True))
  self.defaults.append(("bool", 'abetterpath_track_artist_first', False))
  self.defaults.append(("str",  'abetterpath_track_artist_separator', " - "))
  self.defaults.append(("bool", 'abetterpath_track_tag_filename', True))
  self.defaults.append(("list", 'abetterpath_artist_sort_prefix_list',  self.writeList(['A', 'An', 'The'])))
  self.defaults.append(("list", 'abetterpath_album_date_formats', self.writeList(['%Y-%m-%d', '%Y-%m', '%Y'])))
  self.defaults.append(("dict", 'abetterpath_album_release_status_list', self.writeList({'bootleg': 'Bootleg', 'promotion': 'Promo'})))
  self.defaults.append(("list", 'abetterpath_album_release_type_compilation', self.writeList(['album', 'single', 'ep', 'live', 'other'])))
  self.defaults.append(("list", 'abetterpath_album_release_type_list', self.writeList(['Single', 'EP', 'Remix', 'Live'])))
  self.defaults.append(("list", 'abetterpath_album_compilation_excluded', self.writeList(['remix'])))
  self.defaults.append(("list", 'abetterpath_album_release_type_reverse', self.writeList(['Live'])))
  self.defaults.append(("list", 'abetterpath_album_release_status_reverse', self.writeList([''])))
  self.defaults.append(("list", 'abetterpath_album_catalog_order', self.writeList(['catalognumber', 'barcode', 'asin', 'date', 'totaltracks', 'releasetype'])))
  lists = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lists')
  for infile in os.listdir(lists):
   if os.path.splitext(infile)[1].lower() == ".txt":
    if os.path.isfile(os.path.join(lists, infile)):
     nameSplit = infile.rsplit(".", 1)[0].split("-", 1)
     if len(nameSplit) > 1:
      fileContents = self._readfile(lists, infile, nameSplit[0].lower())
      self.defaults.append((nameSplit[0], "abetterpath_" + nameSplit[1], fileContents))

 def _readfile(self, foldername, filename, fileType = "list", encoding = 'utf-8'):
  with codecs.open(os.path.join(foldername, filename), 'r', encoding) as f:
   return f.read()
  f.closed

 def load(self, setting):
  self.cfg = dict()
  for option in self.defaults:
   try:
    self.cfg[option[1]] = self.readList(setting[option[1]])
   except:
    self.cfg[option[1]] = self.readList(option[2], option[0])

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
      #returndict[split1[1].strip()] = [split2[0].strip(), split2[1].strip()]
      returndict[(split2[0].strip(), split2[1].strip())] = split1[1].strip()
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
     returnstring += key + " = " + value + "\n"
   else: # fileType == "tuple":
    for key, value in inlist.iteritems():
     returnstring += value[0] + ", " + value[1] + " = " + key + "\n"
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
  #self.config.load(album.config.setting)
  self.separator = ","
  self.options = list()
  for option in self.cfg.defaults:
   if option[0] == 'bool':
    self.options.append(BoolOption("setting", option[1], option[2]))
   elif option[0] == 'int':
    self.options.append(IntOption("setting", option[1], option[2]))
   else: # str, list, dict or tuple
    self.options.append(TextOption("setting", option[1], option[2]))

 def load_defaults(self):
  for option in self.cfg.defaults:
   try:
    getattr(getattr(self.ui, option[1]), self.loadVars[option[0]])(option[2]) # self.ui.alpha_number.setChecked(option[2])
   except:
    pass # If there's no control in the UI, don't try to set it!

 def save_defaults(self): # In Windows, saved to HKEY_CURRENT_USER\Software\MusicBrainz\Picard\setting
  for option in self.cfg.defaults:
   self.options.setting[option[1]] = option[2]

 def load(self):
  for option in self.cfg.defaults:
   try:
    getattr(getattr(self.ui, option[1]), self.loadVars[option[0]])(self.options.setting[option[1]]) # self.ui.alpha_number.setChecked(self.options.setting['alpha_number'])
   except:
    try:
     getattr(getattr(self.ui, option[1]), self.loadVars[option[0]])(option[2]) # self.ui.alpha_number.setChecked(self.options.setting['alpha_number'])
    except:
     pass # If there's no control in the UI, don't try to set it!

 def save(self):
  for option in self.cfg.defaults:
   try:
    self.options.setting[option[1]] = getattr(getattr(self.ui, option[1]), self.saveVars[option[0]])() # self.options.setting['alpha_number'] = self.ui.alpha_number.isChecked()
   except:
    #self.options.setting[option[1]] = option[2]  # self.options.setting['alpha_number'] = option[2]
    pass


register_album_metadata_processor(addalbum)
register_track_metadata_processor(addtrack)
register_options_page(abetterpathoptionspage)