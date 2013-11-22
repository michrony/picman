OS:             Win7
<br>
Python version: 2.7
<br>
Utilities used: http://www.sentex.net/~mwandel/jhead/

<b>Usage:</b> picman.py [-h]
<br>
(-mv MV | -mvd MVD | -T | -tS | -ts TS | -jn JN | -jnt | -ju | -jun | -jus | -jp)
<br>
[-jg] [-tbg TBG]
<br>
path

<b>Notes:</b> 
<br>
Image captions are kept in jpg comment or IPTC Caption field. If jpg
comment is empty, IPTC Caption is used. 
<br>

<b>Positional arguments:</b>
<br>
path        files to process

<b>Optional arguments:</b>
<br>
-h, --help  show this help message and exit
<br>
-mv MV      Rename files to prefix.nnn.ext
<br>
-mvd MVD    Rename files to prefix.date.nnn.ext
<br>
-T          Set file mod time from its EXIF info or creation time if no EXIF
<br>
-tS         Create square thumbs: size 120,240
<br>
-ts TS      Create square thumbs with given size
<br>
-jn JN      Create new descriptor *.dscj.txt
<br>
-jnt        Create new descriptors *.dscj.txt from *.dsc.txt
<br>
-ju         Update existing descriptors *.dscj.txt
<br>
-jun        Recreate descriptors *.dscj.txt, renumber images
<br>
-jus        Update existing descriptors *.dscj.txt, split last group of images
<br>
-jp         Put comments from the given *.dscj.txt to jpg's
<br>
-jg         Try copying image files specified in *.dscj.txt from ./bak to this dir
<br>
-tbg TBG    Background color code for thumbs. Default is #c0c0c0
