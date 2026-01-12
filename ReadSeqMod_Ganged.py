##########################
##
## ReadSeqMod_Ganged.py
##
## Written by J. E. Franklin 02/2020 (jfranklin at g.harvard.edu)
##
## Version 3.0 - Updated by LRG to read in ganged files
## 
## Version 2.1 Changed to fix conflict with Python3
##
## Version 2.0 Rewritten as function rather than 
##
## Version 1.3 Bug fix for meta data byte order issues
##
## Version 1.2 Modified to use class objects and read frame meta data
##
## Version 1.1 Modified to be useful for both cameras.
##
## Version 1.0 Original Code to work with early test data from o2 sensor
##
################################

import struct
import numpy as np
import datetime as dt


class Sequence():
  pass

class FrameMeta():
  pass


def ParseFrame(framenum,gang_num,sub_num,height,width,bindata):
  
  #print('Full frame #: '+str(framenum))
  #print('Sub frame # :'+str(sub_num))
  
  Meta = FrameMeta()
  
  
  # Grab time stamp from the last extra 6 bytes (One timestamp for each FULL frame, applied to each subframe)
  temp = struct.unpack_from('<lh',bindata[-6:])
  Meta.timestamp = dt.datetime(1970,1,1) + \
              dt.timedelta(seconds=temp[-2],microseconds=temp[-1]*1000)

  
  #The number of DATA rows for each subframe (assuming last line of each subframe is meta data)
  sub_rows = int((height-gang_num)/gang_num)
  
  #Number of pixels and data size in a subframe
  subframe_pixels = int(sub_rows*width)
  fmt = '<{}h'.format(subframe_pixels)
  fmtsize = struct.calcsize(fmt)
  
  #Number of pixels and datasize in a meta row
  meta_pixels = width
  meta_fmt = '<{}h'.format(meta_pixels)
  meta_fmtsize = struct.calcsize(meta_fmt)
  
  # PROOF OF CORRECT INDICES
  '''for g in range(0,4):
      print('Data = ['+str((fmtsize*g+meta_fmtsize*g))+':'+str(fmtsize*(g+1)+meta_fmtsize*g)+']')
      print('Meta = ['+str(fmtsize*(g+1)+meta_fmtsize*g)+':'+str((fmtsize*(g+1))+meta_fmtsize*((g+1)))+']')'''
      
  #Get the image data of the given subframe
  dataraw = bindata[(fmtsize*sub_num+meta_fmtsize*sub_num):(fmtsize*(sub_num+1)+(meta_fmtsize*sub_num))]
  data_temp = struct.unpack_from(fmt,dataraw)
  data = np.reshape(data_temp,(sub_rows,width))

  # Grab Meta Data for the given subframe -- Not all of this seems to have real data in it
  metaraw = bindata[(fmtsize*(sub_num+1)+meta_fmtsize*sub_num):(fmtsize*(sub_num+1)+(meta_fmtsize)*(sub_num+1))]
  meta_temp = struct.unpack_from(meta_fmt,metaraw)
  metaraw = struct.pack('>{}h'.format(width),*meta_temp)
    
  #Reaad all of the metadata
  Meta.partNum = metaraw[2:34].decode('ascii').rstrip('\x00')
  Meta.serNum = metaraw[34:48].decode('ascii').rstrip('\x00')
  Meta.fpaType = metaraw[48:64].decode('ascii').rstrip('\x00')
  #print(Meta.partNum)
  #print(Meta.serNum)
  #print(Meta.fpaType)
  Meta.crc = struct.unpack_from('>I',metaraw[64:68])[0]
  Meta.frameCounter = struct.unpack_from('>i',metaraw[68:72])[0]
  Meta.frameTime = struct.unpack_from('>f',metaraw[72:76])[0]
  Meta.intTime = struct.unpack_from('>f',metaraw[76:80])[0]
  Meta.freq = struct.unpack_from('>f',metaraw[80:84])[0]
  Meta.boardTemp = struct.unpack_from('>f',metaraw[120:124])[0]
  Meta.rawNUC = struct.unpack_from('>H',metaraw[124:126])[0]
  Meta.colOff = struct.unpack_from('>h',metaraw[130:132])[0]
  Meta.numCols = struct.unpack_from('>h',metaraw[132:134])[0] + 1
  Meta.rowOff = struct.unpack_from('>h',metaraw[136:138])[0]
  Meta.numRows = struct.unpack_from('>h',metaraw[138:140])[0] + 1
  timelist = struct.unpack_from('>7h',metaraw[192:206])
  Meta.yr = timelist[0]
  Meta.dy = timelist[1]
  Meta.hr = timelist[2]
  Meta.mn = timelist[3]
  Meta.sc = timelist[4]
  Meta.ms = timelist[5]
  Meta.microsec = timelist[6]
  Meta.fpaTemp = struct.unpack_from('>f',metaraw[476:480])[0]
  Meta.intTimeTicks = struct.unpack_from('>I',metaraw[142:146])[0]

  return [data,Meta]

#Default to non-ganged images unless given otherwise
def ReadSeq(seqfile,gang_num=1):

  ## Pull camera (ch4 v o2) and sequence timestamp from filename.
  temp = seqfile.split('/')[-1]
  temp = temp.split('_camera_')
  Seq = Sequence()
  Seq.Camera = temp[0]
  Seq.SeqTime = dt.datetime.strptime(temp[1].strip('.seq'),'%Y_%m_%d_%H_%M_%S')

  ## Open file for binary read
  fin = open(seqfile,'rb')
  binhead = fin.read(8192)

  ## Grab meta data for sequence file.
  temp = struct.unpack('<9I',binhead[548:548+36])
  Seq.ImageWidth = temp[0]
  Seq.ImageHeight = temp[1]
  Seq.ImageBitDepth = temp[2]
  Seq.ImageBitDepthTrue = temp[3]
  Seq.ImageSizeBytes = temp[4]
  Seq.NumFrames = temp[6]
  Seq.TrueImageSize = temp[8]
  Seq.NumPixels = Seq.ImageWidth*Seq.ImageHeight
  
  ## Read raw frames
  rawframes = [fin.read(Seq.TrueImageSize) for i in range(Seq.NumFrames)]
  fin.close()

  ## Process each frame -- dropping filler bytes before passing raw
  print('Reading {} ganged frames'.format(Seq.NumFrames))
  print('Converting to {} un-ganged frames'.format(Seq.NumFrames*gang_num))
  
  #List structure to hold each frame
  frames = []
  
  #Iterate over the number of total frames and the number of ganged frames in each full frame (extra 6 bytes = time stamps on full frames)
  for fn in range(Seq.NumFrames):
      for sub_num in range(0,gang_num):
          frames.append(ParseFrame(fn,gang_num,sub_num,Seq.ImageHeight,Seq.ImageWidth,rawframes[fn][:Seq.ImageSizeBytes+6]))
  
  #Strucutre data and meta to be returned
  Data = np.array([dd[0] for dd in frames])
  Meta = [dd[1] for dd in frames]

  return(Data,Meta,Seq)


