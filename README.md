OS:             Win10
<br>
Python version: 3.9
<br>
Utilities used: http://www.sentex.net/~mwandel/jhead/
<pre>
usage: picman.py [-h]
                 (-mv | -mvc | -mvt | -mvd | -T | -tS | -ts TS | -jn | -jnt | -ju | -jue | -jun | -jp | -2ftp | -gpsn GPSN | -gpsu | -gpsg)
                 [-jg] [-pi] [-tbg TBG]

Notes: (1) *.dscj.txt should be always present in curr dir. It is used for jpg renaming and keeps JSON descriptor. If
IPTC is empty, jpg comment is used.

optional arguments:
  -h, --help  show this help message and exit
  -mv         Rename *.jpg files to prefix.nnn.ext
  -mvc        Rename *.jpg files to lower case, replace non-alphanum characters by dots
  -mvt        Rename *.jpg files to yyyy.mm.dd.hhmmss.jpg
  -mvd        Rename *.jpg files to prefix.nnn.date.ext
  -T          Set file mod time from its EXIF info or creation time if no EXIF
  -tS         Create square thumbs: size 240
  -ts TS      Create square thumbs with given size
  -jn         Create new descriptor *.dscj.txt
  -jnt        Create new descriptor *.dscj.txt from *.dsc.txt
  -ju         Update existing descriptor *.dscj.txt
  -jue        Same as -ju plus create envelope around json in *.dscj.txt
  -jun        Recreate descriptor *.dscj.txt, renumber images
  -jp         Put comments from the given *.dscj.txt to jpg's
  -2ftp       Copy *.jpg images to proper ftp subdirectory
  -gpsn GPSN  Create new descriptors *.gps.txt *.gps.htm from Android *.csv files. The value is dst offset for Zulu
  -gpsu       Update descriptors *.gps.txt *.and gps.htm, put *.gps.txt info to image files
  -gpsg       Create descriptors *.gps.txt *.and gps.htm from *.jpg
  -jg         Try copying image files specified in *.dscj.txt from ./bak to this dir
  -pi         Use Picasa-generated index
  -tbg TBG    Background color code for thumbs. Default is #c0c0c0</pre>  
