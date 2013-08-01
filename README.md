OS:             Win7
<br>
Python version: 2.7
<br>
Utilities used: http://www.sentex.net/~mwandel/jhead/

Usage: picman.py [-h]
<br>
                 (-mv MV | -mvd MVD | -T | -tS | -ts TS | -jn JN | -jnt | -ju | -jun | -jus | -jp)
<br>
                 [-jg] [-tbg TBG]
<br>                 
                 path

Notes: 
<br>
(1) Image captions are kept in jpg comment fields or in XPTitle. If jpg
comment is empty, XPTitle is used. 
<br>
(2) XPTitle can be accessed as
Properties/details/Title and in Picasa as Caption, jpg comments - using
IfranView Image/Information/Comment.

positional arguments:
<br>
  path        files to process
<br>
optional arguments:
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
