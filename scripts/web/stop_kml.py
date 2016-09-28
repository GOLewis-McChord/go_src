import copy
import re
import sys

from pykml.factory import KML_ElementMaker as KML
from lxml import etree
from xml.sax.saxutils import unescape

import src.scripts.stop.stop as st
import src.scripts.web.web_pages as web
from src.scripts.constants import PATH


# Function to add style maps for changing the color of the buttons
def add_style(doc, color, highlight):

    # Add the normal style for the KML
    doc.append(KML.Style(
        KML.IconStyle(
            KML.color(color),
            KML.scale(1.1),
            KML.Icon(
                KML.href('http://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png')
            ),
            KML.hotspot('', x='16', y='31', xunits='pixels', yunits='insetPixels'),
        ),

        KML.LabelStyle(
            KML.scale(1.1)
        ),

        id='icon-503-{}-normal'.format(color)))

    # Add the highlight style for the KML
    doc.append(KML.Style(
        KML.IconStyle(
            KML.color(highlight),
            KML.scale(1.1),
            KML.Icon(
                KML.href('http://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png')
            ),
            KML.hotSpot('', x='16', y='31', xunits='pixels', yunits='insetPixels'),
        ),

        KML.LabelStyle(
            KML.scale(1.1)
        ),

        id='icon-503-{}-highlight'.format(highlight)))

    # Set the style map
    doc.append(KML.StyleMap(
        KML.Pair(
            KML.key('normal'),
            KML.styleUrl('#icon-503-{}-normal'.format(color))
        ),

        KML.Pair(
            KML.key('highlight'),
            KML.styleUrl('#icon-503-{}-highlight'.format(highlight))
        ),

        id='icon-503-{}'.format(color)))

    return doc


table = web.stop_schedule()

doc = KML.Document(KML.name("GO Transit Stops"))

# For each unique point of (stop, gps_ref)
for obj in st.Point.objects:
    stop = st.Point.objects[obj]
    # If the stop is available and has valid gps coordinates
    if st.convert_gps_dms_to_dd(stop.gps_n) and st.convert_gps_dms_to_dd(stop.gps_w) and stop.available == '1':

        # Add a placemark in the KML file
        doc.append(KML.Placemark(
            KML.name('({}{}) {}'.format(stop.stop_id, stop.gps_ref, stop.name)),
            KML.description('<![CDATA[<p>http://jblmmwr.com/golewismcchord/transit/stops/{}{}.html</p>{}]]>'.format(
                stop.stop_id, stop.gps_ref, table[(stop.stop_id, stop.gps_ref)])),
            KML.styleUrl('#icon-503-ff777777'),
            KML.Point(
                KML.coordinates('{},{},0'.format(st.convert_gps_dms_to_dd(stop.gps_w),
                                                 st.convert_gps_dms_to_dd(stop.gps_n)))
            )
        ))

doc = add_style(doc, 'ff777777', 'ff555555')
doc = add_style(doc, 'ffA9445A', 'fff2dede')

# Send KML file to string and replace spurious \
kml = KML.kml(doc)
kml = etree.tostring(kml, pretty_print=True).decode('utf-8', errors='strict').replace('\\', '')

# Add encoding line
final = ["<?xml version='1.0' encoding='UTF-8'?>"]

# Unescape the CDATA description HTML
for line in re.split('\n', kml):
    if re.search('\<description\>', line):
        final.append(unescape(line))
    else:
        final.append(line)

# Write the file
writer = open('{}/reports/stops/stops.kml'.format(PATH), 'w')
writer.write('\n'.join(final))

writer = open('{}/src/static/kml/stops.kml'.format(PATH), 'w')
writer.write('\n'.join(final))


