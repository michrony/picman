OS:             Win10
<br>
Utilities used: http://www.sentex.net/~mwandel/jhead/
<pre>
version: 07/22/2024 Python: 3.11.5
usage: picman.py [-h]
                 (-mv | -mvc | -mvt | -mvd | -T | -tS | -ts TS | -jn | -jnb | -ju | -jue | -jun | -jp | -2ftp | -ftp2 | -ftpd | -gpsn | -gpsu | -gpsg | -gpsgh | -cr2 | -mvcr2)
                 [-ex] [-pi] [-pv] [-tbg TBG]

Notes: (1) *.dscj.txt should be always present in curr dir. It is used for jpg
renaming and keeps JSON descriptor. If IPTC is empty, jpg comment is used.

options:  -h, --help  show this help message and exit
  -mv         Rename *.jpg files to prefix.nnn.ext
  -mvc        Rename *.jpg files to lower case, replace non-alphanum characters by dots
  -mvt        Rename *.jpg files to yyyy.mm.dd.hhmmss.jpg
  -mvd        Rename *.jpg files to prefix.nnn.date.ext
  -T          Set file mod time from its EXIF info or creation time if no EXIF
  -tS         Create square thumbs: size 240
  -ts TS      Create square thumbs with given size
  -jn         Create new descriptor *.dscj.txt
  -jnb        Create new descriptor *.dscj.txt from *.body.txt
  -ju         Update existing descriptor *.dscj.txt
  -jue        Same as -ju plus create envelope around json in *.dscj.txt
  -jun        Recreate descriptor *.dscj.txt, renumber images
  -jp         Put comments from the given *.dscj.txt to jpg's
  -2ftp       Copy *.jpg images to proper ftp subdirectory
  -ftp2       Copy *.jpg images from proper ftp subdirectory
  -ftpd       Delete *.jpg images from proper ftp subdirectory
  -gpsn       Create new descriptors *.gps.txt *.gps.htm from Android *.csv files
  -gpsu       Update descriptors *.gps.txt, *.gps.htm, put *.gps.txt info to image files
  -gpsg       Create descriptors *.gps.txt, *.gps.htm from *.jpg
  -gpsgh      Create descriptor gps.htm from *.jpg
  -cr2        Rename images in ./cr2 if necessary
  -mvcr2      ./cr2/*.jpg => ./*.jpg
  -ex         Run mkexif for -mvc
  -pi         Use Picasa-generated index
  -pv         Preview version of *.gps.txt, iptcs not used
  -tbg TBG    Background color code for thumbs. Default is #c0c0c0
  </pre>
