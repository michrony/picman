#!/usr/bin/python

# picman.py
# Picture Manager: process image descriptors, rename, create thumbs

# Utilies used: jhead

# Version 07/18/2011
# Version 08/02/2011: introduced thumb control
# Version 08/15/2011: minor fix: process file names with different capitalization
# Version 11/12/2011: introduced file rename
# Version 02/18/2012: thumb alignment is always done internally using PIL
# Version 11/06/2012: introduced jpg comments from XPTitle field
# Version 12/23/2012: set mod times from creation times if no EXIF 
# Version 12/31/2012: only centered thumbs are prepared 
# Version 01/03/2013: use PIL to extract jpg comments and DateTimeOriginal; added -bg option 
# Version 01/10/2013: fixed PIL/EXIF processing exceptions 
# Version 01/25/2013: added processing of json descriptors *.dscj.txt
# Version 02/06/2013: new/updated *.dscj.txt descriptor is always regrouped
# Version 02/20/2013: enabled argparse, removed obsolete options
# Version 03/24/2013: introduced JsondscSplitLastGroup
# Version 06/01/2013: renamed to picman, modified -jn to specify the descriptor name
# Version 06/04/2013: added image renumbering
# Version 06/11/2013: thumbs recreated after image renumbering
# Version 10/25/2013: use Picasa/IPTC captions, abandon XPTitle field
# Version 10/29/2013: fixed unnecessary warnings for IPTC captions
# Version 04/22/2014: update get json descriptor
# Version 06/15/2014: implemented renaming in place (when certain file names don't change)
# Version 06/06/2015: introduced utf8
# Version 07/16/2016: introduced processing of Picasa-generated index
# Version 07/23/2016: instead of old JsondscSplitLastGroup logic, empty captions are made " ". 
#                     now -jun produces the correct image groups
#                     enable full Picasa processing of IPTC captions 
# Version 09/05/2016: rename modified to order dated images properly
# Version 06/19/2017: added notes processing
# Version 07/09/2017: added -mvd nand to get rid of non-alphanum characters in file names
# Version 07/30/2017: added -jue. Now only -jue produces envelope around json desc in *.dscj.txt
#                     To simplify correcting JSON syntax, -jn, -ju, -jun produce pure JSON in *.dscj.txt
# Version 11/18/2017: use split() instead of beautifulsoup to extract jpg's from Picasa index
# Version 11/19/2017: Win7 / CentOS version
# Version 03/25/2018: changed CLI to use pre-existing *.dscj.txt
#                     path arg retired
#                     now -mvc implements nand funcionality
# Version 03/30/2018: added -mvt option and renameExifTime() 
# Version 07/01/2018: added getting notes from pre-existing *.dscj.txt
# Version 08/11/2018: added setDesc() to create descriptor if non-existent
# Version 10/22/2018: process .*jpg files
#                     Picasa index.html ===> index.bak
# Version 12/17/2018: updated utf8()
# Version 08/19/2019: begin enabling gps captions
# Version 09/04/2019: disable IPTC warnings
# Version 09/15/2019: gps captions ver 1: introduced *.gps.txt, *.gps,.htm desciptors
# Version 09/21/2019: gps update / fix: -gpsn, -ghpsg, -gpsu
#                     -mvt removed, use -mvd instead

#----------------------------------------------------------------------------------------------------------
import sys, os, glob, re, time, json
import copy, uuid
import shutil
import argparse
from   PIL import Image
from   time import sleep
from   datetime import datetime, timedelta
import csv
from   iptcinfo import IPTCInfo
import pprint
import validators

# For Win ActivePython run:
# To install PIL, run PIL-1.1.7.win32-py2.7.exe http://www.pythonware.com/products/pil/
# pypm install iptcinfo
# pip install validators

# For CentOS:
# yum -y install python-pip  - if necessary
# yum install jhead
# pip install Pillow
# pip install iptcinfo
# pip install validators

#----------------------------------------------------------------------------------------------------
# all symbols after x'80' => HTML encoding $#xxx;
def utf8(str): return str.decode('utf_8').encode('ascii', 'xmlcharrefreplace')
#----------------------------------------------------------------------------------------------------------
# Prepare thumb by resizing the image and 
# placing it in the center of properly colored square
def ThumbC(imgI, Tsize, bgColor):

 th = "_t"
 if (Tsize!=120):          th = "__t"
 if (imgI.find(".jpg")>0): imgO = imgI.replace(".jpg", th + ".jpg")
 else:                     imgO = imgI.replace(".JPG", th + ".JPG")
 print "picman: %s=>%s" % (imgI, imgO)

 blank = Image.new('RGB', (Tsize, Tsize), bgColor)
 img   = Image.open(imgI)
 width, height = img.size
 if (width>=height): 
     THUMB_SIZE = (Tsize, (Tsize*height)/width) 
     BOX        = (0, (Tsize - THUMB_SIZE[1])/2)
 else:              
     THUMB_SIZE = ((width * Tsize)/height, Tsize)
     BOX        = ((Tsize - THUMB_SIZE[0])/2, 0)
 
 step = 0
 try:
	img.thumbnail(THUMB_SIZE)
	step = 1
	blank.paste(img, BOX)
	step = 2
	blank.save(imgO) 
 except Exception, e:
    print "ThumbC(): failed step %d - %s" % (step, str(e)) 
    sys.exit()	
 return
#----------------------------------------------------------------------------------------------------------
# Try to get Picasa/IPTC captions for jpg's with empty comments in List
def checkCaptions(List):
   for i in range(0, len(List)):
       iptc = iptcGet(List[i][0])[0]
       curr = List[i][1]
       # if (curr==""): curr = iptc  # use IPTC only if nothing was found in jpg comment 
       if (iptc!=" "): curr = iptc   # if there is IPTC data, use it
       if (curr==""): curr = " " # return blank instead of empty
       List[i][1] = curr
     
   #print List
   return List
#----------------------------------------------------------------------------------------------------------
def getimage(fname):
 if (os.path.exists(fname) or not os.path.exists("./bak/" + fname)): return
 shutil.copy2("./bak/" + fname, "./")
 print  "getimage(): %s copied" % (fname)
 return
#----------------------------------------------------------------------------------------------------------
# Regroup L: 
# put in each row of L maximum number of comment-pic groups, 
# so that each row has no more than MaxNPics pics.
# Returns the rearraged list and its # emty slots 
def JsondscRegroup(L, MaxNPics):

 # Prepare list of comment-iems groups 
 groups = []
 for row in L:
    curr = []
    for el in row:
        if (not el.endswith(".jpg") and len(curr)>0): 
           groups.append(curr)
           curr = []
        curr.append(el)
    if (len(curr)>0): groups.append(curr)  

 LOut = []
 Out  = []
 NPics    = 0
 OutNPics = 0
 MaxLen   = MaxNPics
 for gr in groups:
    #print "MaxNPics: %s OutNPics: %s %s" % (MaxNPics, OutNPics, str(gr))
    NPics = NPics + len(gr)-1
    if (OutNPics>=MaxNPics):
       LOut.append(Out)                # LOut <= Out
       Out = []
       OutNPics = 0
    if (OutNPics+len(gr)-1<=MaxNPics):
       Out      = Out + gr             # Out  <= gr 
       OutNPics = OutNPics + len(gr)-1
       continue      
    if (len(gr)-1>=MaxNPics and OutNPics==0):
       LOut.append(gr)                 # LOut <= gr
       MaxLen = max(MaxLen, len(gr)-1)
       continue
    if (len(gr)-1>=MaxNPics and OutNPics>0):
       LOut.append(Out)
       Out      = []
       OutNPics = 0
       LOut.append(gr)
       MaxLen = max(MaxLen, len(gr)-1)
       continue
    LOut.append(Out)                   # LOut <= Out
    MaxLen = max(MaxLen, len(gr)-1)
    OutNPics = len(gr)-1
    Out      = gr

 if (len(Out)>1): 
    LOut.append(Out)

 NEmpty = MaxLen*len(LOut)-NPics
 print "JsondscRegroup(): MaxNPics=%s MaxLen=%s NEmpty=%s" % (MaxNPics, MaxLen, NEmpty)

 return [LOut, NEmpty] 
#----------------------------------------------------------------------------------------------------------
# Choose regrouping with minimal NEmpty
def JsondscRegroupMin(Rows, MaxNPics):
 NEmpty = 1000
 LOut   = []
 for i in range(0, 3):
     R = JsondscRegroup(Rows, MaxNPics-i)
     if (NEmpty>R[1]): 
        NEmpty = R[1]
        LOut   = R[0]

 return LOut
#----------------------------------------------------------------------------------------------------------
# *.dsc.txt => *.dscj.txt
# Use when JSON descriptor is not available
def JsondscFromText(dscname, MaxNPics, getimages):
 if (not dscname.endswith(".dsc.txt")): 
    print "picman.JsondscFromText: wrong %s" % (dscname)
    return
 F = open(dscname)
 try:    L = F.readlines()
 except: 
         print "JsondscFromText(): failed to read %s" % (dscname)
         return
 
 # ASCII descriptor => list of comment-pics rows 
 Rows = []
 for el in L:
   if (el.find(".jpg")<=0): continue # ignore line without pics
   el = el.replace("]", "")
   el = el.replace("[", "")
   el = el.replace("_t.jpg", ".jpg")
   el = el.replace("http://images/", "")
   #print "==>" + el
   comment = ""
   if (el.find(":")>=0):
      tmp     = el.split(":")
      comment = tmp[0]
      pics    = tmp[1]
   else: pics = el
   row = [comment] + pics.split()
   Rows.append(row)
 
 #print Rows 
 LOut = JsondscRegroupMin(Rows, MaxNPics)

 # Prepare the JSON descrptor file 
 Out   = {dscname.replace(".dsc.txt", ""): LOut}
 fname = dscname.replace(".dsc.txt", ".dscj.txt")
 json.dump(Out, open(fname, "w"), indent=1, sort_keys=True)

 JsonDscProcs(fname, 0, getimages, None) # process new descriptor immediately
#----------------------------------------------------------------------------------------------------------
# Get comments from jpg files and their IPTC.Caption's 
# Create json descritor *.dscj.txt
def GetJpgComments(descname, List, MaxNPics, getimages):

 Res = []

 # get comments from jpg files in List
 for fname in List:
  if fname.lower().endswith("_t.jpg"): continue # ignore thumbs
  try: 
     app     = Image.open(fname).app
  except:
     print "GetJpgComments(): failed to process %s" % (fname)
     exit(0)
  comment = ""
  if ("COM" in app): comment = app["COM"].replace("\x00", "")
  Res.append([fname, comment])

 if len(Res)==0:
    return

 Res = checkCaptions(Res)

 # prepare the descriptors 
 #print "=>" + str(Res)
 Out   = ""
 LOut  = []
 Curr  = []
 #print Captions
 for el in Res:
     #print el
     fname = el[0]
     el[0] = el[0].replace(".jpg", "_t.jpg")
     if el[1]!="":
        if (len(Curr))>0: LOut.append(Curr)
        Curr = []
        try: 
             Out = Out + "\n" + el[1] + ": http://images/" + el[0]
             Curr = [el[1], fname]
        except:
             Out = Out + "\n : http://images/" + el[0]
             Curr = [el[1], fname]
             print "GetJpgComments(): Wrong symbol in %s comment" % (fname)
     else: 
        Out = Out + " http://images/" + el[0]
        Curr.append(fname)
 
 Out = Out[1:] + "\n"
 if (len(Curr)>0): LOut.append(Curr)

 LOut1 = JsondscRegroupMin(LOut, MaxNPics)

 # Prepare the descriptors
 LOut = {descname : LOut1}
 LOut["notes"] = [["", ""], ["", ""]]
 
 # try to get notes from pre-existing desc
 fs = 0
 tmp = {}
 try: 
     fs = os.path.getsize(descname + ".dscj.txt")
 except: pass
 if (fs>0): tmp = JsonDscGet(descname + ".dscj.txt")
 if ("notes" in tmp):
    LOut["notes"] = copy.deepcopy(tmp["notes"]) 
    print "GetJpgComments(): got pre-existing notes"
 
 json.dump(LOut, open(descname + ".dscj.txt", "w"), indent=1, sort_keys=True, encoding ="latin1")
 JsonDscProcs(descname + ".dscj.txt", 0, getimages, None) # process new descriptor immediately

 return len(Res)
#----------------------------------------------------------------------------------------------------------------\
# JSON row => HTML table
def JsonRowProcs(row, getimages):
 if (row[0].endswith(".jpg")): row = [""] + row

 # Prepare the list of comment-items groups 
 groups = []
 curr = []
 for el in row:
   if (not el.endswith(".jpg") and len(curr)>0): 
      groups.append(curr)
      curr = []
   curr.append(el)
 if (len(curr)>0): groups.append(curr)  
    
 # Prepare HTML table for this JSON row
 cell_size = 120 
 anormfmt  = "<a target=win_link href=./images/%s.jpg><img class=th_small src=./images/%s_t.jpg><span><img src=./images/%s__t.jpg></span></a>"
 aviewfmt  = "<a target=win_link href=./%s.jpg><img class=th_small src=./%s_t.jpg><span><img src=./%s__t.jpg></span></a>"
 tdheadfmt = "<td id=tdc colspan=%s width=%s>%s</td>\n"
 tdmainfmt = "<td id=tdi><div class=th_big>%s</div></td>\n"
 trfmt     = "<tr>%s</tr>\n"
 tablefmt  = "<table id=tabi>\n%s%s</table>\n"
 Res_norm  = ""
 Res_view  = ""
 header    = ""
 main_norm = ""
 main_view = ""

 for gr in groups:
   ncols = len(gr)-1
   gr = procGroup(gr)
   for el in gr:
      # prepare header and main rows     
      if (not el.endswith(".jpg")):
         header = header + tdheadfmt % (ncols, ncols*cell_size, el)
         continue
      if (getimages): getimage(el)
      el    = el.replace(".jpg", "")
      anorm = anormfmt % (el, el, el) 
      aview = aviewfmt % (el, el, el) 
      main_norm = main_norm + tdmainfmt % (anorm)
      main_view = main_view + tdmainfmt % (aview)

 header    = trfmt % (header)
 main_norm = trfmt % (main_norm)
 main_view = trfmt % (main_view)
 Res_norm  = Res_norm + tablefmt % (header, main_norm)
 Res_norm  = Res_norm.replace("\n</tr>", "</tr>")   
 Res_view  = Res_view + tablefmt % (header, main_view)
 Res_view  = Res_view.replace("\n</tr>", "</tr>")

 return [Res_norm, Res_view]
#----------------------------------------------------------------------------------------------------------------\
def procGroup(L):
 print "procGroup(): " + str(L)
 return L
#----------------------------------------------------------------------------------------------------------------\
# Get json descriptor from the given file and return the dict
def JsonDscGet(fname):

 try:
   F   = open(fname)
   # get json descriptor
   F_  = " " + utf8(F.read()) + " "
   # get json descriptor
   if ("<!--dscj" in F_): 
      F_  = F_.split("<!--dscj")
      if ("-->" in F_[1]): F_ = F_[1].split("-->")
      else:                F_ = F_[1].split("->")
   else: F_ = [F_]
   IN  = json.loads(F_[0])
   F.close()
 except Exception as e:
   print "JsonDscGet(): Wrong %s - %s" % (fname, str(e))
   return {}
 
 return IN
#----------------------------------------------------------------------------------------------------------------\
# Update *.dscj.txt to include HTML tables
# Create *.dscj.htm to view the images in the current directory
def JsonDscProcs(fname, MaxNPics, getimages, env):

 IN = JsonDscGet(fname)
 if (IN=={}): return
 
 NOTES = []
 if ("notes" in IN):
    NOTES = IN["notes"]
    del IN["notes"]
 
 if (len(IN.keys())!=1): 
    print "JsonDscProcs(): Wrong #keys in %s" % (fname)
    return 

 INkey = IN.keys()[0]
 IN1 = IN[INkey]
 if (MaxNPics>0):             
   IN1 = JsondscRegroupMin(IN1, MaxNPics)

 Res_norm  = ""
 Res_view  = ""
 for row in IN1:
   [norm, view] = JsonRowProcs(row, getimages)
   Res_norm = Res_norm + norm
   Res_view = Res_view + view
 
 Res_notes = NotesProcs(NOTES)
   
 # Write .dscj.txt
 IN1 = {INkey: IN1}
 if (len(NOTES)>0):
    IN1["notes"] = NOTES

 print "JsonDscProcs(): env=" + str(env)
 jdump    = json.dumps(IN1, indent=1, sort_keys=True)
 if (env): 
    Res_norm = "<!--%s\n%s\n-->\n%s" % ("dscj", jdump, Res_norm)
    Res_norm = Res_notes.replace("<br>", "") + Res_norm
 else: 
    Res_norm = jdump
    
 fname_norm = INkey + ".dscj.txt"
 try:
    F = open(fname_norm, "w")
    F.write(utf8(Res_norm))
    F.close()
 except Exception as e:
   print "JsonDscProcs(): failed to write %s - %s" % (fname_norm, e)
    
 # Write .dscj.htm
 fmt       = ""
 scriptdir = os.path.dirname(os.path.realpath(__file__))
 fmtfile   = scriptdir.replace("\\", "/") + "/picman.htm"
 try:
   F   = open(fmtfile)
   fmt = F.read()
   F.close() 
 except:
   print "JsonDscProcs(): failed to read " + fmtfile
   return

 Res_view = Res_notes + Res_view
 Res_view = "<!--%s\n%s\n-->\n%s" % ("dscj", json.dumps(IN, indent=1, sort_keys=True), Res_view)
 if (fmt!=""): Res_view = fmt % (INkey, INkey, Res_view)
 fname_view = INkey + ".dsc.htm"
 try:
    F = open(fname_view, "w")
    F.write(utf8(Res_view))
    F.close()
 except Exception as e:
   print "JsonDscProcs(): failed to write %s - %s" % (fname_view, str(e))
   return
   
 print "JsonDscProcs(): %s, %s created" %(fname_norm, fname_view)
 return
#----------------------------------------------------------------------------------------------------------------
# Check and process the notes pairs
def NotesProcs(IN):

 # Check that this is a list of [string, string] pairs
 if (not IN.__class__.__name__=="list"):
        print "NotesProcs(): Wrong notes in %s" % (el)
        pprint.pprint(In[el])
        return ""
 
 for el in IN:
        if (not el.__class__.__name__=="list"):
           print "NotesProcs(): Wrong note %s" % (el)
           pprint.pprint(el_)
           return ""
        if (len(el)!=2):
           print "NotesProcs(): Wrong note %s" % (el)
           pprint.pprint(el)
           return ""
        str = el[1].__class__.__name__=="str" or el[1].__class__.__name__=="unicode"  
        if (el[0].__class__.__name__!="str" and not str ):
           print "NotesProcs(): Wrong note (%s, %s) in %s" % (el[0].__class__.__name__, el[1].__class__.__name__, el)
           pprint.pprint(el)
           return ""
        if (not el[1]=="" and not validators.url(el[1])):
           print "NotesProcs(): Wrong note [%s, %s]" % (el[0], el[1])
           return ""
  
 res = ""
 for el in IN:
        if (el[0]=="" and el[1]==""): continue
        if (el[0]==""):
           res = res + el[1] + "<br>\n"
           continue
        if (el[1]==""):
           res = res + el[0] + "<br>\n"
           continue
        res = res + el[0] + ": " + el[1] + "<br>\n"
 
 #print "NotesProcs(): res=" + res;
 print "NotesProcs(): %d notes processed" % (len(IN))
 return res
#----------------------------------------------------------------------------------------------------------------
# Put comments into jpg's for this JSON descriptor using jhead
def JsondscPutComments(fname):

 IN     = JsonDscGet(fname)
 INkeys = IN.keys()
 if ("notes" in INkeys): 
    INkeys.remove("notes")
 if (len(INkeys)!=1): 
    print "JsondscPutComments(): wrong keys in desc"
    pprint.pprint(INkeys)
    return 

 INkey  = INkeys[0]
 IN     = IN[INkey]

 N = 0
 comment = " "
 for row in IN:
   for fn in row:
     if (not fn.endswith(".jpg")):
       comment = fn
       continue
     if not os.path.exists(fn):
       print "JsondscPutComments(): stop - %s not found" % (fn)
       return
     cmd = "jhead -cl \"%s\" %s" % (comment, fn)
     os.popen(cmd)
     iptcSet(fn, comment, None)
     N = N + 1
     comment = " "

 print "JsondscPutComments(): %s images processed" % (N)

 return
#----------------------------------------------------------------------------------------------------------------\
# Renumber the images in fname and recreate it
def JsondscRenum(fname):

 IN = JsonDscGet(fname)
 NOTES = []
 if ("notes" in IN):
    NOTES = IN["notes"]
    del IN["notes"]
    
 if (len(IN.keys())!=1): 
    print "JJsondscRenum(%s): wrong descriptor len=%d" % (fname, len(IN.keys()))
    return []

 INkey = IN.keys()[0]
 IN    = IN[INkey]
 Pics  = []
 OUT   = []
 Wrong = [] # non-existent pictures if any
 for group in IN:
     for el in group:
         OUT.append(el)
         if (el.endswith(".jpg")): 
            if (not os.path.exists(el)): Wrong.append(el) 
            Pics.append(el)
            el_t  = el[0:len(el)-4] + "_t.jpg"          #remove thumbs
            el__t = el[0:len(el)-4] + "__t.jpg"
            if (os.path.exists(el_t)):  os.remove(el_t)
            if (os.path.exists(el__t)): os.remove(el__t)

 if (len(Wrong)>0): 
    print "JsondscRenum() failed. The following files do not exist: %s" % (str(Wrong))
    return []

 # renumber the files 
 prefix = str(uuid.uuid4())
 rename(False, prefix, Pics)
 List = glob.glob(prefix + ".*.jpg")
 List.sort()
 rename(False, INkey, List)
 List = glob.glob(INkey + ".*.jpg")
 List.sort()
 Pics = copy.deepcopy(List)

 # prepare the new descriptor
 RES = []
 for el in OUT:
        if (not el.endswith(".jpg")): RES.append(el)
        else: RES.append(List.pop(0))

 OUT = {}
 OUT[INkey] = [RES] 
 if (len(NOTES)>0):
     OUT["notes"] = NOTES
 json.dump(OUT, open(fname, "w"), indent=1, sort_keys=True)

 # remove extra images if any
 N = len(Pics) + 1
 while (os.path.exists("%s.%03d.jpg" % (INkey, N))):
       os.remove("%s.%03d.jpg" % (INkey, N))
       N = N + 1
 
 print "JsondscRenum(): %s images processed. %s extra images removed" % (len(Pics), N-len(Pics)-1)

 return Pics
#----------------------------------------------------------------------------------------------------------------\
def procPicasaIndex(fname):

 print "procPicasaIndex(): try using Picasa-generated %s" % (fname)
 L = []
 if (not os.path.exists(fname)): 
    print "procPicasaIndex(): %s not found" % (fname)
    return L

 try:
    F  = open(fname, "r")
    F_ = utf8(F.read().lower())
    F.close()
    L_ = []
    if ("img" in F_): L_ = F_.split("<img ")[1:]
    for item in L_:
        if (not "src=" in item): continue
        item = item.split("src=")[1]
        if (not ".jpg" in item): continue
        item = item.split(".jpg")[0] + ".jpg"
        item = item.split("/")[-1]
        item = item.replace("_", ".")
        ok   = not item in L and os.path.exists(item)
        if (not ok): 
           L = []
           print "procPicasaIndex(): wrong item " + item
           break
        L.append(item)
 except Exception, e:
    L = []
    print "procPicasaIndex(): wrong %s: %s" % (fname, str(e)) 

 if (len(L)==0): print "procPicasaIndex(): cannot use %s" % (fname)
 else:
    fnbak = fname.replace(".html", ".bak")
    if (os.path.exists(fnbak)): os.remove(fnbak)
    os.rename(fname, fnbak)
    print "procPicasaIndex(): %s ===> %s" % (fname, fnbak)
 
 return L
#----------------------------------------------------------------------------------------------------------------\
# Rename files in List to: prefix.nnn[.date].ext
# For prefix = "": replace non-alphanum characters by dots.
def rename(addDate, prefix, List):
 fname = ""
 if (".htm" in List[0]): fname = List[0] 
 if (fname!=""):  
    List = procPicasaIndex(fname)
 if (fname!="" and len(List)>0):
    print "rename(): use %s, %d items" % (fname, len(List))

 if (len(List)==0):
    print "rename(): nothing to process"
    return 0

 # Prepare new names
 print "rename(): %d items to process" % (len(List))
 InPlace = False
 uid     = str(uuid.uuid4()).split("-")[0] + "."
 N       = 0
 List_   = []
 for el in List:
    if (el.lower().endswith("_t.jpg")): # no thumbs in the list
       os.remove(el)
       continue 
    N      = N + 1
    el     = el.replace("\\", "/")
    el_    = el.split("/")
    el_    = el_[0:len(el_)-1]
    el_    = "/".join(el_)
    if (el_!=""): el_ = el_ + "/"
    ext    = el.split(".")
    ext    = ext[len(ext)-1]
    
    now    = ""
    if addDate:
       nowsec = os.path.getmtime(el)
       now    = "." + time.strftime('%Y.%m.%d', time.localtime(nowsec))
       
    if (prefix!=""): name = el_ + "%s.%.03d%s.%s" % (prefix.lower(), N, now, ext.lower())
    else:            name = (re.sub('[^a-zA-Z0-9]', '.', el)).lower()
    if (name.startswith(".")): name = "0" + name
    #print "=>%s: %s*%s" % (prefix, name, el)
        
    if (name!=el and os.path.exists(name)): 
       InPlace = True
    if (name!=el):     
       List_.append([el, name])

 if (InPlace): print "rename(): in place - stage 1" 
 else:         
    uid = ""
    print "rename(): do it" 
 List = List_   
 for el in List:
    name = uid + el[1]
    if (os.path.exists(name)): os.remove(name) 
    print "rename(): %s=>%s" % (el[0], name)
    os.rename(el[0], name)

 if (not InPlace): return N

 print "rename(): in place - stage 2"
 for el in List:
    if (el[0]==""): continue
    name    = el[1] 
    tmpname = uid + el[1]
    if (os.path.exists(name)): os.remove(name) 
    
    print "rename(): %s=>%s" % (tmpname, name)
    tryMore = False
    try: 
       os.rename(tmpname, name)
    except:
       tryMore = True
    if (tryMore):
       sleep(0.75)
       try: 
          os.rename(tmpname, name)
       except:   
          print "rename(): %s=>%s failed 2 times" % (tmpname, name)
          
    name_t  = name[0:len(name)-4] + "_t.jpg"          #remove thumbs
    name__t = name[0:len(name)-4] + "__t.jpg"
    if (os.path.exists(name_t)):  os.remove(name_t)
    if (os.path.exists(name__t)): os.remove(name__t)

 return N
#----------------------------------------------------------------------------------------------------------
# Group is a list, its head is caption, tail is captioned images
# Find the first image if any with gps info and make caption a hyperlink to Google Maps.
def procGroup(gr):
 if (len(gr)<2): 
    print "procGroup(): wrong group " + str(gr)
    return
 
 if ("empty" in gpsDesc): iniGpsDesc()
 if ("empty" in gpsDesc): return

 (head, tail) = (gr[0], gr[1:])
 found = ""
 for el in tail:
     if (el in gpsDesc):
        found = gpsDesc[el]
        break
 if (found==""): return gr
 
 fmatGooMaps = "https://www.google.com/maps/?q=%s"
 fmatA       = "<a target=win_link href=%s>%s</a>"
 
 link = found
 if (not link.startswith("http")): link = fmatGooMaps % (link)
 
 if (head.strip()==""): head = "map"
 head = fmatA % (link, head)
 
 gr[0] = head
 #print "dbg " + str(gr)
 return gr
#----------------------------------------------------------------------------------------------------------
# Initialize gpsDesc for procGroup()
gpsDesc = {"empty": 1}
def iniGpsDesc(): 
 global gpsDesc
 desc = getGpsDesc()
 if (desc==None or not "dst" in desc or not "root" in desc): return
  
 desc = desc["root"]
 for item in desc:
     if (item[-1]=="y"): 
        gpsDesc[item[1]] = item[3] 
 
 if (len(gpsDesc.keys())>1): del gpsDesc["empty"]
 #print "iniGpsDesc()" + gpsDesc
 print "iniGpsDesc() %d items in gpsDesc" % (len(gpsDesc.keys()))
 
 return
#----------------------------------------------------------------------------------------------------------
# Create json descriptor *.gps.txt with links to Google maps. Use csv files from GPS Logger. 
# dst - offset for Zulu, Ljpg - list of jpg's in this dir
def crGpsDesc(dst, Ljpg):
 if (dst==None): return
 
 Lcsv = glob.glob("*.csv")
 if (len(Lcsv)==0):
    print "crGpsDesc(): no csv to process"
    return

 print "crGpsDesc(): dst=" + str(dst)

 res = []
 # add image items
 for item in Ljpg:
         if (item.endswith("_t.jpg")): continue
         t = getExiTime(item)
         if (t==""): continue
         t = t.replace(" ", ".")
         t = t.replace(":", "")
         res.append([t, None, None, item, "jpg"])

 if (len(Ljpg)==0):
    print "crGpsDesc(): no jpg to process"
    return
         
 for fn in Lcsv:
     curr = [] 
     try:
       with open(fn, "rb") as f:
            reader = csv.reader(f)
            for row in reader: curr.append(row)
     except Exception, e:
            print "crGpsDesc(): Failed to read %s - %s" % (fn, str(e))
            continue

     if (len(curr)<2 or len(curr[0])<3 or curr[0][0]!="time" or curr[0][1]!="lat" or curr[0][2]!="lon"):
        print "crGpsDesc(): Wrong %s" % (fn)
        continue
     curr.pop(0)

     print "crGpsDesc(): %s processed, %d lines" % (fn, len(curr))
     # Prepare res with dst-adjusted dates
     for line in curr:
         if (len(line)<3):
             print "crGpsDesc(): Wrong %s - line too short" % (fn)
             break
         (date, lat, lon) = (line[0], line[1], line[2])
         date_ = date.replace("Z", "UTC")
         date_ = datetime.strptime(date_, "%Y-%m-%dT%H:%M:%S.%f%Z")
         date_ = date_+ timedelta(hours=dst)
         date1 = date_.strftime("%Y%m%d.%H%M%S")
         date2 = date_.strftime("%Y-%m-%d %H:%M:%S")
         # print "dbg: " + date + "=>" + date1 + " " + date2
         res.append([date1, lat, lon, date2, "gps"])
     
 res.sort()
 print "crGpsDesc(): total processed items: %d" % (len(res))
 for i in range(0, len(res)): # mark gps items - neighbours of jpg's
          if (res[i][4]!="jpg"): continue
          currDate = datetime.strptime(res[i][0], "%Y%m%d.%H%M%S")
          left  = findLeftCsv(res, i)
          right = findRightCsv(res, i)
          #print "dbg: %d left=%d right=%d" % (i, left, right)
          if (left>=0 and right>=0):
             leftDate = datetime.strptime(res[left][0], "%Y%m%d.%H%M%S")
             rightDate = datetime.strptime(res[right][0], "%Y%m%d.%H%M%S")
             # print "dbg: leftDate=%s rightDate=%s currDate=%s" % (leftDate, rightDate, currDate)
             leftSub = (currDate - leftDate).total_seconds()
             rightSub = (rightDate - currDate).total_seconds()
             if (leftSub<rightSub): right = -1
             else: left = -1
          if (left>=0):  
              res[i][1] = left
              leftDate  = datetime.strptime(res[left][0], "%Y%m%d.%H%M%S")
              res[i][2] = int((currDate-leftDate).total_seconds())
          if (right>=0): 
              res[i][1] = right
              rightDate = datetime.strptime(res[right][0], "%Y%m%d.%H%M%S")
              res[i][2] = int((rightDate-currDate).total_seconds())

 nimg = 0
 desc = []
 for line in res:
           if (line[4]!="jpg"): continue
           nimg = nimg + 1
           #print line
           t = line[0]
           (Y, M, D, h, m, s) = (t[0:4], t[4:6], t[6:8], t[9:11], t[11:13], t[13:15])
           date = Y + "-" + M + "-" + D + " " + h + ":" + m + ":" + s
           gpsLine = res[line[1]]
           desc.append([nimg, line[3], date, gpsLine[1] + "," + gpsLine[2], line[2], "y"])

 desc = {"dst": dst, "root": desc} 
 desc = json.dumps(desc, indent=1, sort_keys=True) 

 fn = os.getcwd().replace("\\", "/").replace("_", "")
 fn = fn.split("/")[-1] + ".gps.txt"
 
 try:
   f = open(fn, "w")
   f.write(desc)
   f.close()
 except Exception as e:
   print "crGpsDesc(): failed to write %s - %s" % (fn, str(e))
   return
   
 print "crGpsDesc(): %s created, %d images processed" % (fn, nimg)

 return
#--------------------------------------------------------------------------------------
def findLeftCsv(L, ind):
 for i in range(ind-1, -1, -1):
    if (L[i][4].startswith("gps")): return i
 return -1
#--------------------------------------------------------------------------------------
def findRightCsv(L, ind): 
 for i in range(ind+1, len(L)):
    if (L[i][4].startswith("gps")): return i
 return -1 
#--------------------------------------------------------------------------------------
# Create *.gps.htm from json descriptor *.gps.txt
def crGpsHtm():
 desc = getGpsDesc()
 if (desc==None): return
 if (not "dst" in desc or not "root" in desc):
   print "crGpsDesc(): wrong json in %s" % (fn, str(e))
   return

 # prepare html
 maxDelta = 10*60 # max difference between image time and closest gps tick, seconds
 dst = desc["dst"]
 root = desc["root"]

 html = '''
 <html>
 <head>
 <style>
 p{border-style:solid; border-width:2; margin:5; padding:5; display:table}
 img{height:480}
 table{width:100%}
 </style>
 </head>
 <body>
 <h3>Geolocated Images</h3>
 GPS info from: <a target=win00 href=https://play.google.com/store/apps/details?id=com.mendhak.gpslogger&hl=en_US>GPS Logger for Android</a>
 <br/>
 Time zone: UTC[dst] 
 <br/>
 Images: [nimg]
 <br/>
 Use <u>map</u> links to locate images on Google Maps.
 '''
 html = html.replace("[dst]", "%+d" % dst)
 html = html.replace("[nimg]", str(len(root)))
 
 fmatP = '''
 <p title="%s">
 <table><tr>
  <td><b>%s</b></td>
  <td align=center>date: %s</td> 
  <td align=left>delta: %s sec</td> 
  <td align=right>%s</td>
 </tr></table>
 <img src=%s>
 </p>'''
 fmatLink = '''<a style="color:black" target=win00 href=https://www.google.com/maps/?q=%s>map</a>'''
 
 for item in root:
           (num, img, date, coord, delta, active) = (item[0], item[1], item[2], item[3], item[4], "y"==item[5])
           num = "%03d" % (num)
           gpsLink = fmatLink % (coord)
           if (delta>maxDelta): gpsLink = gpsLink.replace("color:black", "color:red")
           if (not active): gpsLink = ""
           p = fmatP % (img, num, date, delta, gpsLink, img)
           html = html + p
 html = html + "</body>\n</html>"   

 fn = os.getcwd().replace("\\", "/").replace("_", "")
 fn = fn.split("/")[-1] + ".gps.htm"
 
 try:
   f = open(fn, "w")
   f.write(html)
   f.close()
 except Exception as e:
   print "crGpsHtm(): failed to write %s" % (fn)
   return
   
 print "crGpsHtm(): %s created" % (fn)
 return
#--------------------------------------------------------------------------------------
# Create json descriptor *.gps.txt from IPTC in *.jpg
def crGpsDescFromJpg(L):
 root = []
 dst  = ""
 nimg = 0
 for fn in L:
   if (not fn.endswith(".jpg") or fn.endswith("_t.jpg")): continue
   (tmp, spinsJ) = iptcGet(fn)
   if (spinsJ.strip()==""):
      print "crGpsDescFromJpg(): %s - can't get IPTC info"
      continue
   try:
      spins = json.loads(spinsJ)
   except Exception as e:
      print "crGpsDescFromJpg(): %s - wrong JSON" % (fn)
      continue
   if (not "dst" in spins or not "root" in spins):
      print "crGpsDescFromJpg(): %s - wrong spins %s" % (fn, str(spins))
      continue
   if (dst!="" and spins["dst"]!=dst):
      print "crGpsDescFromJpg(): %s - wrong spins %s" % (fn, str(spins))
      continue
   dst  = spins["dst"]
   nimg = nimg + 1
   root.append([nimg] + [fn] + spins["root"])
   
 desc  = {"dst": dst, "root": root}
 descJ = json.dumps(desc, indent=1, sort_keys=True)
 #print descJ

 fn = os.getcwd().replace("\\", "/").replace("_", "")
 fn = fn.split("/")[-1] + ".gps.txt"
 
 try:
   f = open(fn, "w")
   f.write(descJ)
   f.close()
 except Exception as e:
   print "crGpsDescFromJpg(): failed to write %s" % (fn)
   return
   
 print "crGpsDescFromJpg(): %s created, %d images processed" % (fn, nimg)
  
 return
#--------------------------------------------------------------------------------------
# Get gps descriptor from file *.gps.txt
def getGpsDesc():
 fn = os.getcwd().replace("\\", "/").replace("_", "")
 fn = fn.split("/")[-1] + ".gps.txt"
 if (not os.path.exists(fn)): 
   print "getGpsDesc(): %s does not exist" % (fn)
   return None
 try:
   f = open(fn, "r")
   desc = f.read()
   f.close()
   desc = json.loads(desc)
 except Exception as e:
   print "getGpsDesc(): failed to get json from %s" % (fn, str(e))
   return None

 return desc   
#--------------------------------------------------------------------------------------
# Save *.gps.txt to proper jpg's
def gpsDesc2jpg():
 desc = getGpsDesc()
 if (desc==None): return 
 if (not "dst" in desc or not "root" in desc):
   print "gpsDesc2jpg(): wrong json in %s" % (fn, str(e))
   return

 (dst, root) = (desc["dst"], desc["root"])
 for item in root:
   fn = item[1]
   out = {"dst": dst, "root": item[2:]}
   out = json.dumps(out)
   #print out
   iptcSet(fn, None, out)
   print "gpsDesc2jpg(): processed %s" % (fn)
   
 return
#--------------------------------------------------------------------------------------
# For files in List, set mod, access times equal to creation time
def setTime(List):
 for f in List: 
       tc = os.path.getctime(f)
       ta = os.path.getatime(f)
       t = min(tc, ta)
       #print "=>tc=%s ta=%s t=%s" % (tc, ta, t)
       t_ = getExiTime(f)
       try:
          t_ = time.strptime(t_, "%Y:%m:%d %H:%M:%S") 
          t_ = time.mktime(t_)
       except:
          print "setTime(): %s - ignore wrong DateTimeOriginal" % (f)
       if (t_!=""): t = t_   
       os.utime(f, (t, t)) # set mod,access times   

 return
#--------------------------------------------------------------------------------------
# Get DateTimeOriginal from EXIF
def getExiTime(fn):
       t = ""
       f = open(fn, "rb") # we need to open and close this file explicitly!
       im = Image.open(f)
       try:    
            exifdata = im._getexif()
            if (exifdata!=None and 36867 in exifdata): 
               #print exifdata
               t = exifdata[36867] # DateTimeOriginal
            if (int(t[:2])>20 or int(t[:2])<19): t = "" 
       except: pass
       f.close()
       return t
#----------------------------------------------------------------------------------------------------------
# Get Picasa/IPTC caption, spec instr from the given file
def iptcGet(fn):
  capt  = None
  spins = None
  info  = None
  sys.stdout = open(os.devnull, 'w') # disable print to block warning msgs
  try:
     info  = IPTCInfo(fn, force=True)
     capt  = info.data['caption/abstract']
     if (not(capt)): capt = " "
     spins = info.data['special instructions']
     if (not(spins)): spins = " "
     sys.stdout = sys.__stdout__ # enable print
  except Exception, e:
     sys.stdout = sys.__stdout__  # enable print
     print "iptcGet() failed to open IPTC in %s - %s" % (fn, str(e))
     return [" ", " "]
  
  capt = capt.strip()
  if (capt==""): capt = " "
  capt = utf8(capt)
  spins = spins.strip()
  if (spins==""): spins = " "
  spins = utf8(spins)
  #print "===>%s/%s" %(fn, capt)
  return [capt, spins]
#----------------------------------------------------------------------------------------------------------
# Put Picasa/IPTC caption and/or special instruction to the given jpg file. 
#     None means don't put this field.
def iptcSet(fn, capt, spins):
  if (capt==None and spins==None): return
  
  if (capt==""):  capt  = " "
  if (spins==""): spins = " "
  now = datetime.now()
  now = now.strftime("%Y%m%d%H%M%S")
  info = None
  sys.stdout = open(os.devnull, 'w') # disable print to block warning msgs
  try:
     n = 1
     info = IPTCInfo(fn, force=True)
     n = 2
     if (capt):  info.data['caption/abstract'] = capt
     if (spins): info.data['special instructions'] = spins
     info.data['date created']     = now
     info.data['writer/editor']    = "picman"
     #info.data['copyright notice'] = ""
     #info.data['keywords']  = ""
     n = 3
     info.save()
     os.remove(fn + "~")
     sys.stdout = sys.__stdout__ # enable print
  except Exception, e:
    info  = None
    sys.stdout = sys.__stdout__  # enable print
    #print "[%s]" % (capt)
    print "iptcSet() failed to process %s - %d %s" % (fn, n, str(e))
  return
#----------------------------------------------------------------------------------------------------
# desc can be info.txt or dscj.txt
# Find matching descriptor in the current dir or create a new one
def setDesc(desc):
 L = glob.glob("*" + desc)
 L.sort()
 res = ""
 if (len(L)>0): 
   res = L[0]
   return res # got desc
   
 # Create new desc using the current dir name
 cwd = os.getcwd().replace("\\", "/").split("/")[-1]
 p = re.compile("[^a-zA-Z0-9\.]")
 res = p.sub("", cwd) + "." + desc

 open(res, 'a').close()
 
 print "setDesc: no descriptor found, created empty " + res
 
 return res # new desc created
#----------------------------------------------------------------------------------------------------
# extract options

notes = '''
Notes:
   (1) *.dscj.txt should be always present in curr dir.
       It is used for jpg renaming and keeps JSON descriptor.
       If IPTC is empty, jpg comment is used.
'''

parser = argparse.ArgumentParser(description=notes)
group  = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-mv',   action="store_true", help="Rename *.jpg files to prefix.nnn.ext")
group.add_argument('-mvc',  action="store_true", help="Rename *.jpg files to lower case, replace non-alphanum characters by dots")
group.add_argument('-mvd',  action="store_true", help="Rename *.jpg files to prefix.nnn.date.ext")
group.add_argument('-T',    action="store_true", help="Set file mod time from its EXIF info or creation time if no EXIF")
group.add_argument('-tS',   action="store_true", help="Create square thumbs: size 120,240")
group.add_argument('-ts',   type=int, help="Create square thumbs with given size")
group.add_argument('-jn',   action="store_true", help="Create new descriptor *.dscj.txt")
group.add_argument('-jnt',  action="store_true", help="Create new descriptor *.dscj.txt from *.dsc.txt")
group.add_argument('-ju',   action="store_true", help="Update existing descriptor *.dscj.txt")
group.add_argument('-jue',  action="store_true", help="Same as -ju plus create envelope around json in *.dscj.txt")
group.add_argument('-jun',  action="store_true", help="Recreate descriptor *.dscj.txt, renumber images") 
group.add_argument('-jp',   action="store_true", help="Put comments from the given *.dscj.txt to jpg's")
group.add_argument('-gpsn', type=int, help="Create new descriptors *.gps.txt *.gps.htm from Android *.csv files. The value is dst offset for Zulu")
group.add_argument('-gpsu', action="store_true", help="Update descriptors *.gps.txt *.and gps.htm, put *.gps.txt info to image files")
group.add_argument('-gpsg', action="store_true", help="Create descriptors *.gps.txt *.and gps.htm from *.jpg")

parser.add_argument('-jg',  action="store_true", help="Try copying image files specified in *.dscj.txt from ./bak to this dir") 
parser.add_argument('-pi',  action="store_true", help="Use Picasa-generated index") 
parser.add_argument("-tbg", type=str, help="Background color code for thumbs. Default is #c0c0c0")
#parser.add_argument("path", type = str, help="files to process")

args = vars(parser.parse_args())

desc = setDesc("dscj.txt")  
print "picman: using " + desc

desc = desc.replace(".dscj.txt", "")  

toSetTime  = args["T"]
Rename     = args["mv"] or args["mvd"] or args["mvc"]
addDate    = args["mvd"]

Tsize     = []
if (args["ts"]!=None): Tsize = [args["ts"]]
if (args["tS"]!=None): Tsize = [120, 240]

bgColor   = "#c0c0c0"
if (args["tbg"]!=None):
   try: 
      tmp     = int(args["tbg"][1:], 16)
      if (len(args["tbg"])==7 and args["tbg"][0]=="#"): bgColor = args["tbg"]
      else: print "picman: Wrong tbg %s assumed %s" % (args["tbg"], bgColor)
   except:
      print "picman: Wrong tbg %s assumed %s" % (args["tbg"], bgColor)
if (args["tbg"]!=None): bgcolor = args["tbg"]

env       = args["jue"]
getimages = args["jg"]
jnew      = args["jn"]
jnewtext  = args["jnt"]
jnum      = args["jun"]
jproc     = args["ju"] or args["jue"] or args["jnt"]
jprocput  = args["jp"]
pi        = args["pi"]

jnewMaxNPics = 6

List = glob.glob("*") # + glob.glob(".*jpg")  
if (pi):
   List = [el for el in List if ("index.htm" in el.lower())]
else: 
   List = [el for el in List if (el.lower().endswith(".jpg"))] # use only jpg files
List.sort()

if (len(List)==0 and not jproc and not jnewtext):
   print "picman: Nothing to process"
   print help
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (jnew):
   print "picman: prepare new json descriptor %s.dscj.txt: %s" % (desc, "*")
   N = GetJpgComments(desc, List, jnewMaxNPics, getimages)
   print "picman: %d processed images" % N
   print "picman: stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (jnewtext):
   fname = desc
   if (not os.path.isfile(desc + ".dsc.txt")):
       print "picman: no %s.dsc.txt - stop" % (desc)
       exit(0)
   print "picman: prepare new json descriptor from: " + fname
   JsondscFromText(desc, jnewMaxNPics, getimages)
   print "picman: stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (jproc or jprocput or jnum):
    Pics = []
    fname = desc + ".dscj.txt"
    if (jnum): 
        print "picman: renumber images using " + fname
        Pics = JsondscRenum(fname)
        if (len(Pics)>0):  
           jproc = True       # create new desc
    if (jproc):
        print "picman: prepare json descriptor " + fname
        JsonDscProcs(fname, jnewMaxNPics, getimages, env)
    if (jprocput): 
        print "picman: %s put comments to images " % (fname)
        JsondscPutComments(fname) 
    if (len(Pics)==0): 
        print "picman: stop"
        exit(0)
    List  = Pics # create new thumbs for pics in List
    Tsize = [120, 240]
#----------------------------------------------------------------------------------------------------------
if (args["gpsn"]):
   crGpsDesc(args["gpsn"], List)
   crGpsHtm()
   print "picman: stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (args["gpsu"]):
   gpsDesc2jpg()
   print "picman: stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (args["gpsg"]):
   crGpsDescFromJpg(List)
   crGpsHtm()
   print "picman: stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (Rename):
   print "picman: rename images"
   if (args["mvc"]): desc = "";
   print "picman: %d processed images" % rename(addDate, desc, List)
   print "picman: stop"
   exit(0)
   
#----------------------------------------------------------------------------------------------------------
if (toSetTime):
   print "picman: Set mod times for %d images: %s" % (len(List), "*")
   setTime(List)
   print "picman: Stop"
   exit(0)
#----------------------------------------------------------------------------------------------------------
if (len(Tsize)>0): 
   print "picman: Prepare thumbs: Tsize=%s bgColor=%s %s" % (str(Tsize), bgColor, "*")
   for imgI in List:
       if (imgI.find("_t.jpg")>0): continue
       if (imgI.find("_t.JPG")>0): continue
       ThumbC(imgI, Tsize[0], bgColor)
       if (len(Tsize)>1): ThumbC(imgI, Tsize[1], bgColor)

if (os.path.exists("picman.log")): os.remove("picman.log")

print "picman: Stop"
exit(0)
#----------------------------------------------------------------------------------------------------------
