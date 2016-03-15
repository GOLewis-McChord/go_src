
import configparser
import csv
import datetime
import os
import re
import sys
import xlsxwriter

import multiprocessing as mp

"""
GO Imports------------------------------------------------------
"""
import src.scripts.transit.constants as System

"""
Main Classes------------------------------------------------------------
"""
class Stop:

    objects = {}
    obj_map = {}
    header = {}

    def __init__(self, stop_id):
        self.stop_id = stop_id
        Stop.objects[stop_id] = self

    @staticmethod
    def map_objects():
        for stop in Stop.objects:
            obj = Stop.objects[stop]
            Stop.obj_map[str(obj.stop_id)] = obj
            try:
                if obj.name:
                    Stop.obj_map[obj.name] = obj
            except:
                raise ValueError('The name for stop ' + str(stop) +
                                 ' does not match between points.')
        return True

class Point:
    
    objects = {}
    header = {}

    def __init__(self, data):
        i = 0
        while i < len(data):
            try:
                exec('self.' + str(Point.header[i]) + '=' +
                     str(data[i]))
                if isinstance(eval('self.' + str(Point.header[i])),
                              complex):
                    exec('self.' + str(Point.header[i]) + '=\'' +
                         str(data[i]) + '\'')
            except:
                exec('self.' + str(Point.header[i]) + '=\'' +
                     str(data[i]) + '\'')
            i += 1
        Point.objects[(str(self.stop_id), str(self.gps_ref))] = self

    @staticmethod
    def process():
        reader = csv.reader(open(System.path + '/data/stops/stops.csv', 'r',
                                 newline=''), delimiter=',', quotechar='|')
        points = []
        for row in reader:
            points.append(row)
        
        # Set header
        i = 0
        while i < len(points[0]):
            Point.header[i] = points[0][i]
            i += 1
            
        # Initialize all other rows as objects
        stops = {}
        for data in points[1:]:
            pt = Point(data)
            if pt.stop_id not in stops:
                stops[pt.stop_id] = {}
            stops[pt.stop_id][pt] = True
            
        # Convert stop DS items to stop objects, will have a feature of data
        # iff all points for the stop have the same value for that feature
        for stop in stops:
            obj = Stop(stop)
            obj._points = stops[stop]
            for feature in Point.header.values():
                match = True
                temp = 'none'
                for pt in obj._points:
                    if temp == 'none':
                        temp = eval('pt.' + str(feature))
                    elif eval('pt.' + str(feature)) != temp:
                        match = False
                if match == True:
                    exec('obj.' + str(feature) + '= temp')

        # Develop object map for stops
        Stop.map_objects()
        return True

class Inventory:

    objects = {}
    tags = {}
    order = ['g', 'f', 'a', 's', 'd', 'i', 'u', 'p', 'n']

    def __init__(self, file):
        self.file = file
        self.records = {}
        self.tags = {}
        Inventory.objects[self.file] = self

    @staticmethod
    def process():
        Inventory.load_codes()
        for dirpath, dirnames, filenames in os.walk(System.path
                                                    + '/data/stops'):
            for filename in [f for f in filenames if re.search(
                'stop_inventory', f)]:
                obj = Inventory((str(dirpath) + '/' + str(filename)))
                obj.read_inventory()
                obj.write_report()
        return True

    @staticmethod
    def load_codes():
        reader = open(System.path + '/data/stops/inventory/inventory_codes',
                      'r')
        for line in reader:
            line = line.rstrip()
            line = re.split('-', line)
            Inventory.tags[line[0].lower()] = line[1]

    def read_inventory(self):
        reader = csv.reader(open(self.file, 'r', newline=''),
                            delimiter=',', quotechar='|')
        self.year = int(self.file[-10:-8]) + 2000
        self.month = int(self.file[-8:-6])
        self.day = int(self.file[-6:-4])
        records = []
        for row in reader:
            records.append(row)
        for line in records[1:]:
            self.records[(line[0], line[1])] = line[2]
            if line[2] not in self.tags:
                self.tags[line[2]] = {}
            self.tags[line[2]][(line[0], line[1])] = True
        return True

    def write_report(self):
        if not os.path.exists(System.path + '/reports/stops/inventory'):
            os.makedirs(System.path + '/reports/stops/inventory')
        writer = open(System.path + '/reports/stops/inventory/Inventory_' +
                      'Report_' + str(self.year) + str(self.month) +
                      str(self.day), 'w')
        for tag in Inventory.order:
            if tag in self.tags:
                writer.write(Inventory.tags[tag] + '\n')
                i = 0
                for stop in sorted(self.tags[tag].keys()):
                    writer.write(stop[0] + stop[1])
                    i += 1
                    if i != len(self.tags[tag]):
                        writer.write(', ')
                    if i % 10 == 0:
                        writer.write('\n')
                writer.write('\n\n')
        writer.close()

def parse_gps_dms(gps):
    return re.split('[\'|\"|°]', re.sub(' ', '', gps))

def convert_gps_dms_to_dd(gps):
    gps = parse_gps_dms(gps)
    return (gps[0] + (gps[1] / 60) + (gps[2] / 3600), gps[3])

def remove_gps_direction(dd_gps):
    if dd_gps[1] == 'N' or dd_gps[1] == 'E':
        return dd_gps[0]
    elif dd_gps[1] == 'S' or dd_gps[1] == 'W':
        return '-' + dd_gps[0]
    else:
        raise ValueError('GPS Point ' + dd_gps + ' has an invalid direction')
    
Point.process()

if __name__ == '__main__':
    Inventory.process()
