##########################
##
## jf_readSeq_v1.3.py
##
## Written by J. E. Franklin 10/2019 (jfranklin at g.harvard.edu)
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
import logging
import sys
import os
import struct
import numpy as np
import argparse
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import statistics

print('\n\nRunning Camera Data Reader (jf_readSeq_v1.3)\n\n')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Sequence():

    ## Set up a class object to hold all frames and sequence header.
    def __init__(self, camera, seqtime, binhead):
        self.Camera = camera
        self.SeqTime = seqtime
        temp = struct.unpack('<9I', binhead[548:548 + 36])
        self.ImageWidth = temp[0]
        self.ImageHeight = int(temp[1])
        self.ImageBitDepth = temp[2]
        self.ImageBitDepthTrue = temp[3]
        self.ImageSizeBytes = int(temp[4])
        self.NumFrames = int(temp[6])
        self.TrueImageSize = int(temp[8])
        self.NumPixels = self.ImageWidth * self.ImageHeight


class FrameObj():

    ## Contains code for stripping meta data off of individual frames.

    def __init__(self, idnum, height, width, bin_image, bin_meta):
        self.id = idnum

        # Calc size of actual image minus meta data
        numpixels = int((height - 1) * width)
        fmt = f'<{numpixels}h'
        data = struct.unpack_from(fmt, bin_image)
        self.data = np.reshape(data, (height - 1, width))

        self.parse_frame_metadata(bin_meta, width)

    def parse_frame_metadata(self, bindata, width):
        """
        Pass the row after the image + the 6 byte timestamp.
        """
        # Grab time stamp
        temp = struct.unpack_from('<lh', bindata[-6:])
        self.timestamp = dt.datetime(1970, 1, 1) + \
                         dt.timedelta(seconds=temp[-2], microseconds=temp[-1] * 1000)
        print(f'Frame #{self.id} at {self.timestamp}')

        # Grab Meta Data -- Not all of this seems to have real data in it.
        metaraw = bindata[:-6]
        temp = struct.unpack_from(f'<{width}h', metaraw)
        metaraw = struct.pack(f'>{width}h', *temp)

        self.partNum = struct.unpack_from('<32s', metaraw[2:34])[0].rstrip(b'\x00')
        self.serNum = struct.unpack_from('<14s', metaraw[34:48])[0].rstrip(b'\x00')
        self.fpaType = struct.unpack_from('<16s', metaraw[48:64])[0].rstrip(b'\x00')
        self.crc = struct.unpack_from('>I', metaraw[64:68])[0]
        self.frameCounter = struct.unpack_from('>i', metaraw[68:72])[0]
        self.frameTime = struct.unpack_from('>f', metaraw[72:76])[0]
        self.intTime = struct.unpack_from('>f', metaraw[76:80])[0]
        self.freq = struct.unpack_from('>f', metaraw[80:84])[0]
        self.boardTemp = struct.unpack_from('>f', metaraw[120:124])[0]
        self.rawNUC = struct.unpack_from('>H', metaraw[124:126])[0]
        self.colOff = struct.unpack_from('>h', metaraw[130:132])[0]
        self.numCols = struct.unpack_from('>h', metaraw[132:134])[0] + 1
        self.rowOff = struct.unpack_from('>h', metaraw[136:138])[0]
        self.numRows = struct.unpack_from('>h', metaraw[138:140])[0] + 1
        self.intTimeTicks = struct.unpack_from('>I', metaraw[142:146])[0]
        timelist = struct.unpack_from('>7h', metaraw[192:206])
        self.yr = timelist[0]
        self.dy = timelist[1]
        self.hr = timelist[2]
        self.mn = timelist[3]
        self.sc = timelist[4]
        self.ms = timelist[5]
        self.microsec = timelist[6]
        self.fpaTemp = struct.unpack_from('>f', metaraw[476:480])[0]


def parse_frames(superframes):
    frames = []
    bytes_per_subframe = int((Seq.NumPixels / superframes - Seq.ImageWidth) * 2)
    bytes_per_meta = Seq.ImageWidth * 2
    for i in range(superframes_to_read):
        timestamp = rawframes[i][Seq.ImageSizeBytes:Seq.ImageSizeBytes + 6]
        for superframe in range(superframes):
            index = int(superframe * (bytes_per_subframe + bytes_per_meta) + bytes_per_subframe)
            frame_metadata = rawframes[i][index:index + bytes_per_meta]
            metadata = frame_metadata + timestamp
            frames.append(FrameObj(
                i, int(Seq.ImageHeight / superframes), Seq.ImageWidth,
                rawframes[i][int(superframe*bytes_per_subframe):int((superframe+1)*bytes_per_subframe)],
                metadata
            ))

    return frames


## Argument Parser
parser = argparse.ArgumentParser(
    description='Reads in 30s sequence file and outputs npy obj of mean',
    epilog='Written by J.Franklin (jfranklin@g.harvard.edu) Oct 2019'
)
parser.add_argument('infile',
                    help='Sequence File to be read and plotted')
parser.add_argument('-p', '--plot', action='store_true',
                    help='Generate Plots')
args = parser.parse_args()

## Identify and confirm sequence file exists.
filepath = args.infile
if not os.path.exists(filepath):
    print(f'ERROR: Unable to find {filepath}')
    sys.exit()

## Pull camera (ch4 v o2) and sequence timestamp from filename.
filename_split = filepath.split('/')[-1]
filename_split = filename_split.split('_camera_')
camera = filename_split[0]
seqdate = dt.datetime.strptime(filename_split[1].strip('.seq'), '%Y_%m_%d_%H_%M_%S')

print(f'Opening: {filepath}')
fin = open(filepath, 'rb')
binhead = fin.read(8192)

superframes = 4
Seq = Sequence(camera, seqdate, binhead)

## Split up data into frames
testing = True
if testing:
    frames_to_read = 1000
    superframes_to_read = int(frames_to_read / superframes)
else:
    superframes_to_read = Seq.NumFrames
rawframes = [fin.read(Seq.TrueImageSize) for i in range(superframes_to_read)]
fin.close()

nframes = Seq.NumFrames

## Read each frame -- dropping filler bytes before passing raw
Seq.frames = parse_frames(superframes)

## Print metadata from first frame if desired
logging.info(f"Metadata:\n{Seq.frames[0].__dict__}")

## Quick basic plot if desired
# if args.plot:
#     plt.figure(1)
#     avgframe = np.log10(avgframe)
#     plt.imshow(avgframe, aspect='auto')
#     plt.title('log10 {} -- {} frames'.format(fout, nframes))
#     plt.show()

# For each frame, use 'yr', 'dy', etc. to get the frame timestamp internal to the camera
# Calculate elapsed time since last frame
# Plot it
# Take average, too
for idx, frame in enumerate(Seq.frames):
    # meta.ts = double(meta.day) * 86400 + double(meta.hour) * 3600 + double(meta.min) * 60 + ...
    # double(meta.sec) + double(meta.millisec) / 1e3 + double(meta.microsec) / 1e6;
    t = frame.dy * 86400 + frame.hr * 3600 + frame.mn * 60 + frame.sc + frame.ms / 1e3 + frame.microsec / 1e6
    Seq.frames[idx].real_timestamp = t

# Convert the frames to a dataframe
df = pd.DataFrame([_.__dict__ for _ in Seq.frames])
logging.info(f"Read {len(df)} frames from a sequence of {len(Seq.frames)} frames.")

if args.plot:
    plt.figure(2)
    plt.plot(df.frameCounter, df.real_timestamp, label="Timestamps")
    plt.title("Calculated Timestamps across frameCounters")
    plt.xlabel('Frame Count')
    plt.ylabel('Timestamp (s)')

    plt.figure(3)
    t_diff = [df.real_timestamp[i] - df.real_timestamp[i - 1] for i in range(1, len(df))]
    plt.plot(df.frameCounter[1:], t_diff)
    plt.xlabel("Frame Count")
    plt.ylabel("Elapsed time between frames (s)")
    plt.title(f"Average frame rate: {1 / statistics.mean(t_diff):.2f} Hz")

    plt.figure(4)
    frame_diff = [df.frameCounter[i] - df.frameCounter[i - 1] for i in range(1, len(df))]
    plt.plot(df.frameCounter[1:], frame_diff)
    plt.xlabel("Frame Count")
    plt.ylabel("frameCounter between frames (s)")
    plt.title(f"Frame Counter Diff")
    plt.show()
