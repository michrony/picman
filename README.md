OS:             Win7
<br>
Python version: 2.7
<br>
Utilities used: http://www.sentex.net/~mwandel/jhead/
<pre>
usage: picman.py [-h]
                 (-mv | -mvc | -mvd | -mvt | -T | -tS | -ts TS | -jn | -jnt | -ju | -jue | -jun | -jp)
                 [-jg] [-pi] [-tbg TBG] [-gps GPS]

Notes: (1) xxx.dscj.txt should be always present in curr dir. It is used for
jpg renaming and keeps JSON descriptor. (2) Image captions are kept in jpg
comment fields or in IPTC. If IPTC is empty, jpg comment is used.

optional arguments:
  -h, --help  show this help message and exit
  -mv         Rename *.jpg files to prefix.nnn.ext
  -mvc        Rename *.jpg files to lower case, replace non-alphanum
              characters by dots
  -mvd        Rename *.jpg files to prefix.nnn.date.ext
  -mvt        Rename *.jpg files using EXIF time
  -T          Set file mod time from its EXIF info or creation time if no EXIF
  -tS         Create square thumbs: size 120,240
  -ts TS      Create square thumbs with given size
  -jn         Create new descriptor *.dscj.txt
  -jnt        Create new descriptor *.dscj.txt from *.dsc.txt
  -ju         Update existing descriptor *.dscj.txt
  -jue        Same as -ju plus create envelope around json in *.dscj.txt
  -jun        Recreate descriptor *.dscj.txt, renumber images
  -jp         Put comments from the given *.dscj.txt to jpg's
  -jg         Try copying image files specified in *.dscj.txt from ./bak to
              this dir
  -pi         Use Picasa-generated index
  -tbg TBG    Background color code for thumbs. Default is #c0c0c0
  -gps GPS    Generate .url's for Google maps from GPS Logger for Android csv
              files. Value is dst offset for Zulu
</pre>  
