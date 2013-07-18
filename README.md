System:         Win7

Python version: 2.7

Utilities used: http://www.sentex.net/~mwandel/jhead/

Usage: picman.py [-h]

                 (-mv MV | -mvd MVD | -T | -tS | -ts TS | -jn JN | -jnt | -ju | -jun | -jus | -jp)

                 [-jg] [-tbg TBG]
                 
                 path

Notes: 

(1) Image captions are kept in jpg comment fields or in XPTitle. If jpg
comment is empty, XPTitle is used. 

(2) XPTitle can be accessed as
Properties/details/Title and in Picasa as Caption, jpg comments - using
IfranView Image/Information/Comment.

positional arguments:

  path        files to process

optional arguments:

  -h, --help  show this help message and exit
  
  -mv MV      Rename files to prefix.nnn.ext
  
  -mvd MVD    Rename files to prefix.date.nnn.ext
  
  -T          Set file mod time from its EXIF info or creation time if no EXIF
  
  -tS         Create square thumbs: size 120,240
  
  -ts TS      Create square thumbs with given size
  
  -jn JN      Create new descriptors *.dscj.txt
  
  -jnt        Create new descriptors *.dscj.txt from *.dsc.txt
  
  -ju         Update existing descriptors *.dscj.txt
  
  -jun        Recreate descriptors *.dscj.txt, renumber images
  
  -jus        Update existing descriptors *.dscj.txt, split last group of
              images
  -jp         Put comments from the given *.dscj.txt to jpg's
  
  -jg         Try copying image files specified in *.dscj.txt from ./bak to
              this dir
  
  -tbg TBG    Background color code for thumbs. Default is #c0c0c0
