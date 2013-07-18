# picman.py
# Picture Manager: process image descriptors, rename, create thumbs

# Utilies used: jhead

# Version 07/18/2011
# Version 08/02/2011: introduced thumb control
# Version 08/15/2011: minor fix: process file names with different capitalization
# Version 08/29/2011: minor fix: get exif from given file
# Version 10/12/2011: introduced jpg comments processing 
# Version 11/12/2011: introduced file rename
# Version 02/18/2012: thumb alignment is always done internally using PIL
# Version 11/06/2012: introduced jpg comments from XPTitle field
# Version 12/23/2012: set mod times from creation times if no EXIF 
# Version 12/31/2012: only centered thumbs are prepared 
# Version 01/03/2013: use PIL to extract jpg comments and DateTimeOriginal; added -bg option 
# Version 01/10/2013: fixed PIL/EXIF processing exceptions 
# Version 01/25/2013: added processing json descriptors *.dscj.txt
# Version 02/06/2013: new/updated *.dscj.txt descriptor is always regrouped
# Version 02/20/2013: enabled argparse, removed obsolete options
# Version 03/24/2013: introduced JsondscSplitLastGroup
# Version 06/01/2013: renamed to picman, modified -jn to specify the descriptor name
# Version 06/04/2013: added image renumbering
# Version 06/11/2013: thumbs recreated after image renumbering

import sys, os, glob, re, time, json
import copy, uuid
import shutil
import argparse
import Image
import pythoncom
from win32com.shell import shell
from win32com import storagecon

import logging

#----------------------------------------------------------------------------------------------------------
# Prepare thumb by resizing the image and 
# placing it in the center of properly colored square
def ThumbC(imgI, Tsize, bgColor):

 th = "_t"
 if (Tsize!=120):          th = "__t"
 if (imgI.find(".jpg")>0): imgO = imgI.replace(".jpg", th + ".jpg")
 else:                     imgO = imgI.replace(".JPG", th + ".JPG")
 print "picman: %s=>%s" % (imgI, imgO)

 blank = Image.new('RGBA', (Tsize, Tsize), bgColor)
 img   = Image.open(imgI)
 width, height = img.size
 if (width>=height): 
     THUMB_SIZE = (Tsize, (Tsize*height)/width) 
     BOX        = (0, (Tsize - THUMB_SIZE[1])/2)
 else:              
     THUMB_SIZE = ((width * Tsize)/height, Tsize)
     BOX        = ((Tsize - THUMB_SIZE[0])/2, 0)
 img.thumbnail(THUMB_SIZE)
 blank.paste(img, BOX)
 blank.save(imgO) 

 return
#----------------------------------------------------------------------------------------------------------
# Get given Win file/properties/property
PROPERTIES = {
  pythoncom.FMTID_SummaryInformation : dict (
    (getattr (storagecon, d), d) for d in dir (storagecon) if d.startswith ("PIDSI_")
  )
}
STORAGE_READ = storagecon.STGM_READ | storagecon.STGM_SHARE_EXCLUSIVE

#----------------------------------------------------------------------------------------------------------
def get_fproperty (property, property_set_storage, fmtid):
  try:
    property_storage = property_set_storage.Open (fmtid, STORAGE_READ)
  except pythoncom.com_error, error:
    if error.strerror == 'STG_E_FILENOTFOUND':
      return ""
    else: raise
      
  fproperty = ""
  for name, property_id, vartype in property_storage:
    if name is None:
     name = PROPERTIES.get (fmtid, {}).get (property_id, None)
    if name!=property: continue
    try:
      for value in property_storage.ReadMultiple ([property_id]):
        if value!="": 
           fproperty = value
    #
    # There are certain values we can't read; they
    # raise type errors from within the pythoncom
    # implementation, thumbnail
    #
    except TypeError:
      print "%s reading failure" % name
  return fproperty
  
#----------------------------------------------------------------------------------------------------------
# Get XPTitle for the given file
def winfiletitle (filepath):
  pidl, flags = shell.SHILCreateFromPath (os.path.abspath (filepath), 0)
  property_set_storage = shell.SHGetDesktopFolder ().BindToStorage (pidl, None, pythoncom.IID_IPropertySetStorage)
  ftitle = ""
  for fmtid, clsid, flags, ctime, mtime, atime in property_set_storage:
    tmp = get_fproperty ("PIDSI_TITLE", property_set_storage, fmtid)
    if tmp!="": 
       ftitle = tmp.strip() # get title stripped from whitespace
       break
  
  return ftitle
#----------------------------------------------------------------------------------------------------------
# Get comments from XPTitle of jpg files in List
def GetWinComments(List):
   Res = {}
   for el in List:
       if el.find("_t.")>0: continue
       Res[el] = winfiletitle(el)

   #print Res
   return Res
#----------------------------------------------------------------------------------------------------------
def getimage(fname):
 if (os.path.exists(fname) or not os.path.exists("./bak/" + fname)): return
 shutil.copy2("./bak/" + fname, "./")
 print  "picman.getimage: %s copied" % (fname)
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
 print "picman.JsondscRegroup: MaxNPics=%s MaxLen=%s NEmpty=%s" % (MaxNPics, MaxLen, NEmpty)

 return [LOut, NEmpty] 
#----------------------------------------------------------------------------------------------------------
# Choose regouping with minimal NEmpty
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
def JsondscFromText(dscname, MaxNPics, getimages, jsplit):
 if (not dscname.endswith(".dsc.txt")): 
    print "picman.JsondscFromText: wrong %s" % (dscname)
    return
 F = open(dscname)
 try:    L = F.readlines()
 except: 
         print "picman.JsondscFromText: cannot read %s" % (dscname)
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

 # Prepare the JSON dscrptor file 
 Out   = {dscname.replace(".dsc.txt", ""): LOut}
 fname = dscname.replace(".dsc.txt", ".dscj.txt")
 json.dump(Out, open(fname, "w"), indent=1, sort_keys=True)

 JsonDscProcs(fname, 0, getimages, jsplit) # process new descriptor immediately
#----------------------------------------------------------------------------------------------------------
# Get comments from jpg files and their XPTitle's 
# XPTtitle is used if there is no jpg comment
# Create json dscritor *.dscj.txt
def GetJpgComments(descname, List, winTitles, MaxNPics, getimages, jsplit):

 Res = []

 # get comments from jpg files in List
 for fname in List:
  if fname.lower().endswith("_t.jpg"): continue # ignore thumbs
  app     = Image.open(fname).app
  comment = ""
  if ("COM" in app): comment = app["COM"].replace("\x00", "")
  Res.append([fname, comment])

 if len(Res)==0:
    return

 # prepare the descriptors 
 #print "=>" + str(Res) + "\n" + str(winTitles)
 Out   = ""
 LOut  = []
 Curr  = []
 #print winTitles
 for el in Res:
     #print el
     if (el[1]=="" and winTitles[el[0]]!=""): el[1] = winTitles[el[0]] # use winTitle to replace empty comments
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
             print "Wrong symbol in %s comment" % (fname)
     else: 
        Out = Out + " http://images/" + el[0]
        Curr.append(fname)
 
 Out = Out[1:] + "\n"
 if (len(Curr)>0): LOut.append(Curr)

 LOut1 = JsondscRegroupMin(LOut, MaxNPics)

 # Prepare the descriptors
 LOut = {descname : LOut1}
 
 json.dump(LOut, open(descname + ".dscj.txt", "w"), indent=1, sort_keys=True)

 JsonDscProcs(descname + ".dscj.txt", 0, getimages, jsplit) # process new descriptor immediately

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
   #print gr
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
# Take the last comment-item group and insert blank comments for its images
# starting from the tail - until the commented image is found
def JsondscSplitLastGroup(IN):
 Last = copy.deepcopy(IN[len(IN)-1])
 rLast = range(0, len(Last))
 rLast.reverse()
 for n in rLast:
   if (not Last[n].lower().endswith(".jpg")): break
   if (n>0 and not Last[n-1].lower().endswith(".jpg")): break
   Last.insert(n, "")
 #print json.dumps(Last, indent=1, sort_keys=True)

 IN[len(IN)-1] = copy.deepcopy(Last)

 return IN
#----------------------------------------------------------------------------------------------------------------\
# Get json descriptor from the given file and return the dict
def JsonDscGet(fname):

 p1 = re.compile("<!--dscj[\s]*{")
 p2 = re.compile("}[\s]*-->")
 try:
   F   = open(fname)
   F_  = F.read()
   F_  = p1.sub("{", F_) # clean json from its envelope
   F_  = p2.split(F_)[0].rstrip()
   if (not F_.endswith("}")): F_ = F_ + "}"
   IN  = json.loads(F_)
   F.close()
 except:
   print "picman.JsonDscGet: Wrong %s" % fname
   return {}
 
 if (len(IN.keys())!=1):
   print "picman.JsonDscGet: Wrong %s" % fname
   return {}

 return IN
#----------------------------------------------------------------------------------------------------------------\
# Update *.dscj.txt to include HTML tables
# Create *.dscj.htm to view the images in the current directory
def JsonDscProcs(fname, MaxNPics, getimages, jsplit):

 IN = JsonDscGet(fname)
 if (len(IN.keys())!=1): return # wrong descriptor

 INkey = IN.keys()[0]
 IN1 = IN[INkey]
 if (MaxNPics>0):             
   if (jsplit): IN1 = JsondscSplitLastGroup(IN1)
   IN1 = JsondscRegroupMin(IN1, MaxNPics)

 Res_norm  = ""
 Res_view  = ""
 for row in IN1:
   [norm, view] = JsonRowProcs(row, getimages)
   Res_norm = Res_norm + norm
   Res_view = Res_view + view

 # Write .dscj.txt
 IN1 = {INkey: IN1}
 Res_norm = "<!--%s\n%s\n-->\n%s" % ("dscj", json.dumps(IN1, indent=1, sort_keys=True), Res_norm)
 fname_norm = INkey + ".dscj.txt"
 try:
    F = open(fname_norm, "w")
    F.write(Res_norm)
    F.close()
 except:
   print "picman.JsonDscProcs: failed to write %s" % fname_norm
    
 # Write .dscj.htm
 fmt       = ""
 scriptdir = os.path.dirname(os.path.realpath(__file__))
 fmtfile   = scriptdir.replace("\\", "/") + "/picman.htm"
 try:
   F   = open(fmtfile)
   fmt = F.read()
   F.close()
 except:
   print "picman.JsonDscProcs: failed to read %s"

 Res_view = "<!--%s\n%s\n-->\n%s" % ("dscj", json.dumps(IN, indent=1, sort_keys=True), Res_view)
 if (fmt!=""): Res_view = fmt % (INkey, INkey, Res_view)
 fname_view = INkey + ".dsc.htm"
 try:
    F = open(fname_view, "w")
    F.write(Res_view)
    F.close()
 except:
   print "picman.JsonDscProcs: failed to write %s" % fname_view

 print "picman: %s, %s created" %(fname_norm, fname_view)
 return
#----------------------------------------------------------------------------------------------------------------\
# Put comments into jpg's for this JSON descriptor
def JsondscPutComments(fname):

 IN = JsonDscGet(fname)
 if (len(IN.keys())!=1): return # wrong descriptor

 INkey = IN.keys()[0]
 IN    = IN[INkey]

 N = 0
 comment = ""
 for row in IN:
   for el in row:
     if (not el.endswith(".jpg")):
       comment = el
       continue
     if not os.path.exists(el):
       print "picman: stop %s not found" % (el)
       return
     cmd = "jhead -cl \"%s\" %s" % (comment, el)
     os.popen(cmd)
     N   = N + 1
     comment = ""

 print "picman: %s images processed" % (N)

 return
#----------------------------------------------------------------------------------------------------------------\
# Renumber the images in fname and reacreate it
def JsondscRenum(fname):

 IN = JsonDscGet(fname)
 if (len(IN.keys())!=1): return # wrong descriptor

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
    print "picman.JsondscRenum failed. The following files do not exist: %s" % (str(Wrong))
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
 #print OUT
 json.dump(OUT, open(fname, "w"), indent=1, sort_keys=True)

 # remove extra images if any
 N = len(Pics) + 1
 while (os.path.exists("%s.%03d.jpg" % (INkey, N))):
       os.remove("%s.%03d.jpg" % (INkey, N))
       N = N + 1
 
 print "picman.JsondscRenum: %s images processed. %s extra images removed" % (len(Pics), N-len(Pics)-1)

 return Pics
#----------------------------------------------------------------------------------------------------------------\
# Rename files in List to: prefix[.date].nnn.ext
def rename(addDate, prefix, List):

 N = 0
 for el in List:
    if (el.lower().endswith("_t.jpg")): 
       os.remove(el)
       continue 
    el     = el.replace("\\", "/")
    el_    = el.split("/")
    el_    = el_[0:len(el_)-1]
    el_    = "/".join(el_)
    if el_!="": el_ = el_ + "/"
    ext    = el.split(".")
    ext    = ext[len(ext)-1]
    N      = N+1
    now    = ""
    if addDate:
       nowsec = os.path.getmtime(el)
       now    = "." + time.strftime('%Y.%m.%d', time.localtime(nowsec))
    name   = el_ + "%s%s.%.03d.%s" % (prefix.lower(), now, N, ext.lower())
    #print "picman.rename: " + el + "=>" + name
    if (os.path.exists(name)): os.remove(name) 
    os.rename(el, name)
    name_t  = name[0:len(name)-4] + "_t.jpg"          #remove thumbs
    name__t = name[0:len(name)-4] + "__t.jpg"
    if (os.path.exists(name_t)):  os.remove(name_t)
    if (os.path.exists(name__t)): os.remove(name__t)

 return N
#----------------------------------------------------------------------------------------------------------
# For files in List, set mod, access times equal to creation time
def setTime(List):

 for f in List: 
       tc = os.path.getctime(f)
       ta = os.path.getatime(f)
       t = min(tc, ta)
       #print "=>tc=%s ta=%s t=%s" % (tc, ta, t)

       # try get DateTimeOriginal from EXIF
       im = Image.open(f)
       if hasattr(im, '_getexif'):
          try:    exifdata = im._getexif()
          except: print "picman: %s wrong EXIF" % f 
          if (exifdata!=None and 36867 in exifdata): 
            #print exifdata
            tc_ = exifdata[36867] # DateTimeOriginal
            #print "%s %s" % (f, tc)
            try:
              tc__ = time.strptime(tc_, "%Y:%m:%d %H:%M:%S") 
              tc__ = time.mktime(tc__) 
              t    = tc__
            except: print "picman: %s ignore wrong DateTimeOriginal %s" % (f, tc_)

       #print t
       os.utime(f, (t, t)) # set mod,access times
 return
#----------------------------------------------------------------------------------------------------------
# extract options

notes = '''
Notes:
(1) Image captions are kept in jpg comment fields or in XPTitle. 
   If jpg comment is empty, XPTitle is used.
(2) XPTitle can be accessed as Properties/details/Title and in Picasa as Caption, 
   jpg comments - using IfranView Image/Information/Comment.'''

parser = argparse.ArgumentParser(description=notes)
group  = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-mv',   help="Rename files to prefix.nnn.ext")
group.add_argument('-mvd',  help="Rename files to prefix.date.nnn.ext")
group.add_argument('-T',    action="store_true", help="Set file mod time from its EXIF info or creation time if no EXIF")
group.add_argument('-tS',   action="store_true", help="Create square thumbs: size 120,240")
group.add_argument('-ts',   type=int, help="Create square thumbs with given size")
group.add_argument('-jn',   type=str, help="Create new descriptors *.dscj.txt")
group.add_argument('-jnt',  action="store_true", help="Create new descriptors *.dscj.txt from *.dsc.txt")
group.add_argument('-ju',   action="store_true", help="Update existing descriptors *.dscj.txt")
group.add_argument('-jun',  action="store_true", help="Recreate descriptors *.dscj.txt, renumber images") 
group.add_argument('-jus',  action="store_true", help="Update existing descriptors *.dscj.txt, split last group of images") 
group.add_argument('-jp',   action="store_true", help="Put comments from the given *.dscj.txt to jpg's")
parser.add_argument('-jg',  action="store_true", help="Try copying image files specified in *.dscj.txt from ./bak to this dir") 
parser.add_argument("-tbg", type = str, help="Background color code for thumbs. Default is #c0c0c0")
parser.add_argument("path", type = str, help="files to process")
args = vars(parser.parse_args())

Path      = args["path"]
toSetTime = args["T"]
Rename    = ""
addDate   = args["mvd"]!=None
if (addDate): Rename = args["mvd"]
if (args["mv"]!=None): Rename = args["mv"]

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

getimages = args["jg"]
jnew      = args["jn"]
jnewtext  = args["jnt"]
jnum      = args["jun"]
jproc     = args["ju"] or args["jnt"] or args["jus"]
jprocput  = args["jp"]
jsplit    = args["jus"]
jnewMaxNPics = 6

List = glob.glob(Path)
List = [el for el in List if (el.lower().endswith(".jpg"))] # use only jpg files
List.sort()
#print "Rename=" + Rename
#print "Path=" + Path

if (len(List)==0 and not jproc and not jnewtext):
   print "picman: Nothing to process"
   print help
   exit(0)

#----------------------------------------------------------------------------------------------------------
if (jnew!=None):
   print "picman: prepare new json descriptor %s.dscj.txt: %s" % (jnew, Path)
   Res    = GetWinComments(List)
   N      = GetJpgComments(jnew, List, Res, jnewMaxNPics, getimages, jsplit)
   print "picman: %d processed images" % N
   print "picman: stop"
   exit(0)

#----------------------------------------------------------------------------------------------------------
if (jnewtext):
   fname = ""
   List = glob.glob(Path)
   for el in List:
       if (el.endswith(".dsc.txt")):
          fname = el
          break  
   if (fname!=""): 
      print "picman: prepare new json descriptor from: " + fname
      JsondscFromText(fname, jnewMaxNPics, getimages, jsplit)
   print "picman: stop"
   exit(0)

#----------------------------------------------------------------------------------------------------------
if (jproc or jprocput or jnum):
    List = glob.glob(Path)
    Pics = []
    for el in List:
        if (el.endswith("dscj.txt")): 
           if (jnum): 
              print "picman: %s renumber images " % (el)
              Pics = JsondscRenum(el)
              if (len(Pics)>0):  
                 jproc = True       # create new desc
           if (jproc):
              print "picman: prepare json descriptor " + el
              JsonDscProcs(el, jnewMaxNPics, getimages, jsplit)
           if (jprocput): 
              print "picman: %s put comments to images " % (el)
              JsondscPutComments(el) 
    if (len(Pics)==0): 
       print "picman: stop"
       exit(0)
    List  = Pics # create new thumbs for pics in List
    Tsize = [120, 240]

#----------------------------------------------------------------------------------------------------------
if Rename!="":
   print "picman: rename files: " + Path
   print "picman: %d processed files" % rename(addDate, Rename, List)
   print "picman: stop"
   exit(0)
   
logging.basicConfig(filename='picman.log', level=logging.CRITICAL)

#----------------------------------------------------------------------------------------------------------
if (toSetTime):
   print "picman: Set mod times for %d images: %s" % (len(List), Path)
   setTime(List)
   print "picman: Stop"
   logging.shutdown()
   os.remove("picman.log")
   exit(0)
    
#----------------------------------------------------------------------------------------------------------
if (len(Tsize)>0): 
   print "picman: Prepare thumbs: Tsize=%s bgColor=%s %s" % (str(Tsize), bgColor, Path)
   for imgI in List:
       if (imgI.find("_t.jpg")>0): continue
       if (imgI.find("_t.JPG")>0): continue
       ThumbC(imgI, Tsize[0], bgColor)
       if (len(Tsize)>1): ThumbC(imgI, Tsize[1], bgColor)

logging.shutdown()
os.remove("picman.log")

print "picman: Stop"
exit(0)
#----------------------------------------------------------------------------------------------------------
