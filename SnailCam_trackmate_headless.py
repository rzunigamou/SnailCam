#@ File(label="Input directory with TIFFs", style="directory") input_dir
#@ File(label="Output TrackMate XML", style="save") output_xml
#@ File(label="Output spots CSV", style="save") output_spots_csv
#@ File(label="Output tracks CSV", style="save") output_tracks_csv

import sys

from ij.plugin import FolderOpener

from fiji.plugin.trackmate import Model, Settings, TrackMate, Logger
from fiji.plugin.trackmate.detection import ThresholdDetectorFactory, DetectorKeys
from fiji.plugin.trackmate.features import FeatureFilter
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking import TrackerKeys
from fiji.plugin.trackmate.io import TmXmlWriter, CSVExporter

# We have to do the following to avoid errors with UTF8 chars generated in 
# TrackMate that will mess with our Fiji Jython.
reload(sys)
sys.setdefaultencoding('utf-8')

# 1) Open stack from folder
imp = FolderOpener.open(input_dir.getAbsolutePath())
if imp is None:
    raise RuntimeError("Could not open image stack from: " + input_dir.getAbsolutePath())

# Treat slices as time frames: C=1, Z=1, T=N
imp.setDimensions(1, 1, imp.getStackSize())

# 2) Configure TrackMate
model = Model()
model.setLogger(Logger.DEFAULT_LOGGER)
settings = Settings(imp)

# Detector: Thresholding detector
settings.detectorFactory = ThresholdDetectorFactory()
detector_settings = settings.detectorFactory.getDefaultSettings()
detector_settings[DetectorKeys.KEY_TARGET_CHANNEL] = 1
detector_settings[ThresholdDetectorFactory.KEY_INTENSITY_THRESHOLD] = 45.0
settings.detectorSettings = detector_settings

# Initial quality threshold
settings.initialSpotFilterValue = 0.0

# Needed for circularity + other features
settings.addAllAnalyzers()

# Spot filters
settings.addSpotFilter(FeatureFilter('RADIUS', 2.8, True))        # radius > 2.8
settings.addSpotFilter(FeatureFilter('RADIUS', 20.0, False))      # radius < 20
settings.addSpotFilter(FeatureFilter('CIRCULARITY', 0.53, True))  # circularity > 0.53

# Tracker: Sparse LAP
tracker_factory = SparseLAPTrackerFactory()
settings.trackerFactory = tracker_factory
tracker_settings = tracker_factory.getDefaultSettings()

tracker_settings[TrackerKeys.KEY_LINKING_MAX_DISTANCE] = 6.0
tracker_settings[TrackerKeys.KEY_GAP_CLOSING_MAX_DISTANCE] = 6.0
tracker_settings[TrackerKeys.KEY_GAP_CLOSING_MAX_FRAME_GAP] = 2
tracker_settings[TrackerKeys.KEY_ALLOW_GAP_CLOSING] = True
tracker_settings[TrackerKeys.KEY_ALLOW_TRACK_SPLITTING] = False
tracker_settings[TrackerKeys.KEY_ALLOW_TRACK_MERGING] = False
settings.trackerSettings = tracker_settings

# 3) Run
trackmate = TrackMate(model, settings)
if not trackmate.checkInput():
    raise RuntimeError(trackmate.getErrorMessage())
if not trackmate.process():
    raise RuntimeError(trackmate.getErrorMessage())

# 3.1) Track filters
settings.addTrackFilter(FeatureFilter('NUMBER_SPOTS', 45, True))

# 4) Save XML
writer = TmXmlWriter(output_xml)
writer.appendModel(model)
writer.appendSettings(settings)
writer.writeToFile()

# 5) Export CSVs via CSVExporter (string paths only)
print(dir(CSVExporter)) #troubleshooting

exporter = CSVExporter()

exporter.exportSpots(output_spots_csv.getAbsolutePath(), model, True)

print("Done.")
print("Visible spots: %d" % model.getSpots().getNSpots(True))
print("Visible tracks: %d" % model.getTrackModel().nTracks(True))
print("XML:    " + output_xml.getAbsolutePath())
print("Spots:  " + output_spots_csv.getAbsolutePath())
print("Tracks: " + output_tracks_csv.getAbsolutePath())