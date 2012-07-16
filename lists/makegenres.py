from xml.dom import minidom
import os

# http://developer.rovicorp.com/siggen
# http://api.rovicorp.com/data/v1/descriptor/musicgenres?include=all&format=xml&apikey=3qjjbgkjms3nc9jcnr2xt5r8&sig=

tuple_genres = ""
dict_genres = ""
list_genres = ""
xml = minidom.parse('genres.xml')
for genre in xml.getElementsByTagName('Genre'):
 g = genre.getElementsByTagName('name')[0].firstChild.data.title()
 tuple_genres += g + ", " + g + " = " + g + "\n"
 dict_genres += g + " = " + g + "\n"
 list_genres += g + "\n"
 for subgenre in genre.getElementsByTagName('subgenre'):
  s = subgenre.getElementsByTagName('name')[0].firstChild.data.title()
  tuple_genres += g + ", " + g + " = " + s + "\n"
  dict_genres += s + " = " + g + "\n"
  list_genres += s + "\n"
  for style in subgenre.getElementsByTagName('style'):
   t = style.getElementsByTagName('name')[0].firstChild.data.title()
   tuple_genres += g + ", " + s + " = " + t + "\n"
   dict_genres += t + " = " + g + "\n"
   list_genres += t + "\n"

#open('tuple-genres.txt', 'w').write(tuple_genres.encode('UTF-8'))
open('dict-tag_genres.txt', 'w').write(dict_genres.encode('UTF-8'))
#open('list-genres.txt', 'w').write(list_genres.encode('UTF-8'))
