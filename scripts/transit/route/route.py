#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

# Python libraries and packages
import copy
import csv
import datetime
import math
import os
import re

# Entire scripts from src
import src.scripts.transit.stop.stop as st
import src.scripts.transit.route.constants as RouteConstants
import src.scripts.transit.route.errors as RouteErrors

# Classes and variables from src
from src.scripts.transit.constants import PATH


class Route(object):

    objects = {}
    header_0 = 'Name'
    header_1 = 'Stop'

    def __init__(self, name, id, desc, color, miles, date, path, data):
        # Attributes from metadata
        self.name = name
        self.id = id
        self.desc = desc
        self.color = color
        self.miles = float(miles)
        self.date = date
        self.path = path

        # Additional attributes
        self.trip_id = 1
        self.stop_times = {}

        # Set objects
        Route.objects[self.name] = self
        Route.objects[self.id] = self

        # Load sheets from data
        self.sheets = {}
        for sheet in data:
            new_sheet = sheet + [self]
            self.sheets[Sheet(*new_sheet)] = True

    def __repr__(self):
        return ('<{} was initialized with service {} and directions of '.format(self.name, self.service) +
                '{} and {}>'.format(self.direction0.name, self.direction1.name))

    @staticmethod
    def process():
        # Load direction and service CSVs
        Direction.load()
        Service.load()

        # Search for route directories in go/data/routes
        for dirpath, dirnames, filenames in os.walk(PATH + '/data/routes'):
            # Only explore subdirectories that match the route{X} format
            for dirname in [d for d in dirnames if re.search('route[\d]*', d)]:

                # Note metadata and logo paths
                with open('{}/{}/metadata.txt'.format(dirpath, dirname), 'r') as f:
                    metadata = f.read()
                logo = '{}/{dirname}/{dirname}_logo.jpg'.format(dirpath, dirname=dirname)

                # Search for YYYYMMDD file collections/subdirectories within the /route{X} subdirectory
                for inner_dirpath, inner_dirnames, inner_filenames in os.walk('{}/{}'.format(dirpath, dirname)):
                    # Only explore subdirectories that match the YYYYMMDD format
                    for inner_dirname in sorted([d for d in inner_dirnames if re.search('\d{8}', d)]):
                        # Only select the folder that matches the date query from route/constants.py
                        date = datetime.datetime.strptime(inner_dirname, '%Y%m%d')
                        if date >= RouteConstants.DATE:

                            # Read the data.csv file
                            data = []
                            reader = csv.reader(open('{}/{}/{}/data.csv'.format(dirpath, dirname, inner_dirname), 'r',
                                                     newline=''), delimiter=',', quotechar='|')
                            for row in reader:
                                data.append(row)

                            # Create Route object
                            args = re.split(',', metadata.rstrip()) + [date, '{}/{}/{}/'.format(dirpath, dirname,
                                                                                                inner_dirname), data]
                            Route(*args)

                            # Break loop so that first match >= constant date is the final selection
                            break

        return True

    def set_order(self, dirnum):
        order = {}
        d = int(dirnum)
        i = 0
        # Set order[travel_time] = stop_id
        for entry in self.data:
            # If stop is operating and not the destination
            if not re.search('[a-z]', entry[d + 1]) and entry[0]:
                order[int(entry[d + 1])] = i
                # If 0 second spread set stop as origin
                if entry[d + 1] == '0':
                    exec('self.origin_stop{}=entry[0]'.format(dirnum))

            # Elif the stop is the destination
            elif re.search('d', entry[d + 1]):
                exec('self.destination_stop{}=entry[0]'.format(dirnum))
                exec('self.trip_length{}=int(re.sub( '.format(dirnum) +
                     '\'d\', \'\', entry[d+1]))')
            i += 1

        # List of stop_ids in order of travel_time
        temp = [order[key] for key in sorted(order.keys())]

        # Convert temp list to dictionary of segment order
        order = {}
        i = 1
        for row_id in temp:
            order[row_id] = i
            i += 1
        exec('self.order{}=order'.format(dirnum))
        return True

    def set_roundtrip(self):
        self.offset0 = int(self.offset)
        for entry in self.data:
            if re.search('d', entry[1]):
                self.roundtrip += (int(re.sub('d', '', entry[1])) / 60)
                self.offset1 = (self.offset0 +
                                (int(re.sub('d', '', entry[1])) / 60)
                                 ) % int(self.headway)
            if re.search('d', entry[2]):
                self.roundtrip += (int(re.sub('d', '', entry[2])) / 60)
        return True

    def set_entries(self):
        # Handle processing for each entry
        i = 0
        for entry in self.data:
            # General record validation
            if entry[0] == Route.header_0:
                continue
            if not re.sub(' ', '', ''.join(str(x) for x in entry)):
                continue

            # Stop validation and mapping
            if str(entry[0]) not in st.Stop.obj_map:
                raise ValueError('Stop ' + str(entry[0]) + ' from file ' +
                                 str(self.data_file) + ' is not recognized.')

            # GPS reference handling
            gps_ref = re.split('&', entry[3])

            # Process entries
            self.set_stop_time((entry[0], gps_ref[0], i), entry[1], self.start,
                               self.end, '0')
            self.set_stop_time((entry[0], gps_ref[1], i), entry[2], self.start,
                               self.end, '1')
            i += 1

        # Convert origin_time value in stop_time to trip_id
        self.set_trip_ids('0')
        self.set_trip_ids('1')
        return True

    def set_stop_time(self, stop, travel_time, start, end, dirnum):
        if re.search('[a-zA-Z]', travel_time):
            return False

        # Base time is start + spread + offset
        base = start + datetime.timedelta(0, (int(travel_time) + (eval(
            'int(self.offset' + dirnum + ')') * 60)))

        # If spread + offset >= headway then reduce base by headway time
        if ((int(travel_time) / 60) + eval('int(self.offset' + dirnum + ')'
                                           ) >= int(self.headway)):
            base = base - datetime.timedelta(0, 60 * int(self.headway))

        # Add stop_times until end time
        while True:
            if base <= end:
                origin = base - datetime.timedelta(0, int(travel_time))
                if stop not in eval('self.stop_time{}'.format(dirnum)):
                    exec('self.stop_time{}[stop]=dict()'.format(dirnum))

                # stop_time0/1[stop][time] = origin_time
                exec('self.stop_time{}[stop][base.strftime(\'%H:%M\')]=origin.strftime(\'%H:%M\')'.format(dirnum))

                # origin0/1[origin_time] = True
                exec('self.origin{}[origin.strftime(\'%H:%M\')]=True'.format(dirnum))
            else:
                break
            base = base + datetime.timedelta(0, 60 * int(self.headway))
        return True

    def set_trip_ids(self, dirnum):
        # Convert origin_time values to trip_ids
        i = 1
        for time in sorted(eval('self.origin{}.keys()'.format(dirnum))):
            # Instantiate a Trip object
            exec('trip=Trip(self.id, self.service, self.direction' + '{}.id, i)'.format(dirnum))
            # Set origin_time to trip_id -> origin0/1[time] = trip_id
            exec('self.origin{}[time]=trip.id'.format(dirnum))

            # Set time as a datetime for comparison
            T = copy.deepcopy(self.date).replace(hour=int(time[0:2]),minute=int(time[-2:]))
            exec('self.time{}[T]=trip.id'.format(dirnum))
            i += 1

        # Instantiate StopTime objects for each stop_time
        for stop in eval('self.stop_time{}'.format(dirnum)):
            for time in eval('self.stop_time{}[stop]'.format(dirnum)):
                # Collect the trip_id based on the origin time
                exec('trip_id=self.origin{dirnum}[self.stop_time{dirnum}[stop][time]]'.format(dirnum=dirnum))

                # Set a StopTime object with all attributes
                exec('StopTime(trip_id, stop[0], stop[1], time, self.order{}[stop[2]], 0, '.format(dirnum) +
                     'self.display[stop[0]])') # FIX THIS ABOUT THE TIMEPOINT TO SET FOR 100, 220, 480, 780
        return True


class Sheet(object):

    objects = {}

    def __init__(self, sheet, service, dir0, dir1, headway, offset, joint, route):
        # Attributes from data.csv
        self.sheet = sheet
        self.service = Service.objects[service]
        self.dir0 = Direction.objects[dir0]
        self.dir1 = Direction.objects[dir1]
        self.headway = headway
        self.offset = offset
        self.joint = joint
        self.route = route

        # Set objects
        Sheet.objects[sheet] = self

        # Attributes from conversion
        self.date = self.route.date
        self.start = copy.deepcopy(self.date).replace(hour=int(self.service.start_time[:-2]),
                                                      minute=int(self.service.start_time[-2:]))
        self.end = copy.deepcopy(self.date).replace(hour=int(self.service.end_time[:-2]),
                                                    minute=int(self.service.end_time[-2:]))
        self.service_text = self.service.text
        self.data, self.schedule, self.display = self.load_data()

        # Attributes from processing
        self.roundtrip = 0
        self.stop_time0 = {}
        self.stop_time1 = {}
        self.origin0 = {}
        self.origin1 = {}
        self.time0 = {}
        self.time1 = {}
        self.stop_times = {}

        # Process
        self.set_order('0')
        self.set_order('1')
        self.set_roundtrip()
        self.set_entries()

    def load_data(self):
        # Load data file for the route
        reader = csv.reader(open('{}{}'.format(self.route.path, self.sheet), 'r', newline=''), delimiter=',',
                            quotechar='|')

        # Set data entries
        data = []
        schedule = {}
        display = {}
        i = 0
        for row in reader:
            if row[0] == Route.header_1:
                continue
            data.append(row)
            schedule[i] = row[0]
            display[row[0]] = display.get(row[0], 0) + int(row[-1])
            i += 1
        return data, schedule, display

    def set_order(self, dirnum):
        order = {}
        d = int(dirnum)
        i = 0
        # Set order[travel_time] = stop_id
        for entry in self.data:
            # If stop is operating and not the destination
            if not re.search('[a-z]', entry[d + 1]) and entry[0]:
                order[int(entry[d + 1])] = i
                # If 0 second spread set stop as origin
                if entry[d + 1] == '0':
                    exec('self.origin_stop{}=entry[0]'.format(dirnum))

            # Elif the stop is the destination
            elif re.search('d', entry[d + 1]):
                exec('self.destination_stop{}=entry[0]'.format(dirnum))
                exec('self.trip_length{}=int(re.sub( '.format(dirnum) +
                     '\'d\', \'\', entry[d+1]))')
            i += 1

        # List of stop_ids in order of travel_time
        temp = [order[key] for key in sorted(order.keys())]

        # Convert temp list to dictionary of segment order
        order = {}
        i = 1
        for row_id in temp:
            order[row_id] = i
            i += 1
        exec('self.order{}=order'.format(dirnum))
        return True

    def set_roundtrip(self):
        self.offset0 = int(self.offset)
        for entry in self.data:
            if re.search('d', entry[1]):
                self.roundtrip += (int(re.sub('d', '', entry[1])) / 60)
                self.offset1 = (self.offset0 +
                                (int(re.sub('d', '', entry[1])) / 60)
                                 ) % int(self.headway)
            if re.search('d', entry[2]):
                self.roundtrip += (int(re.sub('d', '', entry[2])) / 60)
        return True

    def set_entries(self):
        # Handle processing for each entry
        i = 0
        for entry in self.data:
            # General record validation
            if entry[0] == Route.header_0:
                continue
            if not re.sub(' ', '', ''.join(str(x) for x in entry)):
                continue

            # Stop validation and mapping
            if str(entry[0]) not in st.Stop.obj_map:
                raise ValueError('Stop {} from file {} is not recognized.'.format(str(entry[0]), str(self.sheet)))

            # GPS reference handling
            gps_ref = re.split('&', entry[3])

            # Process entries
            self.set_stop_time((entry[0], gps_ref[0], i), entry[1], self.start,
                               self.end, '0')
            self.set_stop_time((entry[0], gps_ref[1], i), entry[2], self.start,
                               self.end, '1')
            i += 1

        # Convert origin_time value in stop_time to trip_id
        self.set_trip_ids('0')
        self.set_trip_ids('1')
        return True

    def set_stop_time(self, stop, travel_time, start, end, dirnum):
        if re.search('[a-zA-Z]', travel_time):
            return False

        # Base time is start + spread + offset
        base = start + datetime.timedelta(0, (int(travel_time) + (eval(
            'int(self.offset' + dirnum + ')') * 60)))

        # If spread + offset >= headway then reduce base by headway time
        if ((int(travel_time) / 60) + eval('int(self.offset' + dirnum + ')'
                                           ) >= int(self.headway)):
            base = base - datetime.timedelta(0, 60 * int(self.headway))

        # Add stop_times until end time
        while True:
            if base <= end:
                origin = base - datetime.timedelta(0, int(travel_time))
                if stop not in eval('self.stop_time{}'.format(dirnum)):
                    exec('self.stop_time{}[stop]=dict()'.format(dirnum))

                # stop_time0/1[stop][time] = origin_time
                exec('self.stop_time{}[stop][base.strftime(\'%H:%M\')]=origin.strftime(\'%H:%M\')'.format(dirnum))

                # origin0/1[origin_time] = True
                exec('self.origin{}[origin.strftime(\'%H:%M\')]=True'.format(dirnum))
            else:
                break
            base = base + datetime.timedelta(0, 60 * int(self.headway))
        return True

    def set_trip_ids(self, dirnum):
        # Convert origin_time values to trip_ids
        for time in sorted(eval('self.origin{}.keys()'.format(dirnum))):
            # Instantiate a Trip object
            exec('trip=Trip(self.route.id, self.service.id, self.dir{}.id, self.route.trip_id)'.format(dirnum))
            # Set origin_time to trip_id -> origin0/1[time] = trip_id
            exec('self.origin{}[time]=trip.id'.format(dirnum))

            # Set time as a datetime for comparison
            T = copy.deepcopy(self.date).replace(hour=int(time[0:2]),minute=int(time[-2:]))
            exec('self.time{}[T]=trip.id'.format(dirnum))
            self.route.trip_id += 1

        # Instantiate StopTime objects for each stop_time
        for stop in eval('self.stop_time{}'.format(dirnum)):
            for time in eval('self.stop_time{}[stop]'.format(dirnum)):
                # Collect the trip_id based on the origin time
                exec('trip_id=self.origin{dirnum}[self.stop_time{dirnum}[stop][time]]'.format(dirnum=dirnum))

                # Set a StopTime object with all attributes
                exec('StopTime(trip_id, stop[0], stop[1], time, self.order{}[stop[2]], 0, '.format(dirnum) +
                     'self.display[stop[0]])') # FIX THIS ABOUT THE TIMEPOINT TO SET FOR 100, 220, 480, 780
        return True


class JointRoute(object):

    objects = {}

    def __init__(self, joint):
        self.joint = joint
        self.routes = self.set_routes()
        self.drivers = self.set_drivers()

        # Derive trips and spread
        self.trips = self.set_trips()
        self.trip_length = self.set_trip_length()

        # Create a dictionary for all trips
        unset = dict((tuple(x), True) for x in self.trips)
        # Delete the first trip which is taken before the order is set
        del unset[tuple(self.trips[0])]

        # Validate that the final trip ends at the origin of the first
        self._joint_origin = self.trips[0][2]
        # Call order function
        self.order = self.set_order(tuple(self.trips[0][0:2]), self.trips[0][3], {}, copy.deepcopy(unset))
        self.back_order = self.set_back_order()
        self.display_order = self.set_display_order()

        # Find first driving start position
        self.anchor = self.set_anchor()
        self.schedules = {}
        self._hidden_key = {}
        self.locations = {}
        self.set_schedules()
        self.disseminate()

        JointRoute.objects[joint] = self

    @staticmethod
    def process():
        for route in Route.objects:
            if Route.objects[route].joint in JointRoute.objects or Route.objects[route].id in JointRoute.objects:
                continue
            elif Route.objects[route].joint != '<null>':
                JointRoute(Route.objects[route].joint)
            else:
                JointRoute(Route.objects[route].id)
        return True

    def set_routes(self):
        # Split out routes from the joint key
        temp = re.split('\&', self.joint)

        # Convert routes to Route objects
        routes = []
        for route in temp:
            routes.append(Route.objects[route])
        return routes

    def set_drivers(self):
        self.roundtrip = 0
        self.headway = self.routes[0].headway

        # Find joint roundtrip
        for route in self.routes:
            if route.headway != self.headway:
                raise RouteErrors.JointHeadwayNotMatchError('The headways for joint key {} do not match.'.format(
                    self.joint))
            self.roundtrip += route.roundtrip

        # Find the number of drivers based on the roundtrip and headway
        drivers = math.ceil(self.roundtrip / self.headway)

        # Convert driver number to range of drivers
        return [x for x in range(1, drivers + 1)]

    def set_trips(self):
        trips = []
        for route in self.routes:
            # Example: ['Route 1', '0', '100', '480']
            trips.append([route.id, '0', route.origin_stop0,
                          route.destination_stop0])
            try:
                trips.append([route.id, '1', route.origin_stop1,
                              route.destination_stop1])
            except:
                pass
        return sorted(trips)

    def set_trip_length(self):
        trip_length = {}
        for route in self.routes:
            trip_length[(route.id, '0')] = (route.trip_length0 / 60)
            try:
                trip_length[(route.id, '1')] = (route.trip_length1 / 60)
            except:
                pass
        return trip_length

    def set_order(self, key, next, order, unset):
        """
        The set_order is a recursive function that attempts to link
        trips for the JointRoute object. Note that these trips are not
        the same as the Trip class in Route.py. There is only one trip
        for each direction instead of a trip for each headway in each
        direction.
        :param next: The previous destination and origin of next trip.
        :return: True when executed properly, exceptions may be raised.
        """
        # Base case - no more trips need to be set
        if not unset:
            if next != self._joint_origin:
                raise RouteErrors.JointRoutesNotMatchError('Trips from joint key {} do not have '.format(self.joint) +
                                                           ' matching origin and destination values.')
            order[key] = tuple(self.trips[0][0:2])
            return order

        # Find acceptable trips
        for option in unset:
            if option[2] == next:
                # Set new values
                new_key = tuple(option[0:2])
                new_next = option[3]

                # Deepcopy the order and add current trip
                new_order = copy.deepcopy(order)
                new_order[key] = new_key

                # Deepcopy unset and del current trip
                new_unset = copy.deepcopy(unset)
                del new_unset[option]

                # Recurse with updated order
                return self.set_order(new_key, new_next, new_order, new_unset)

        # If no trips were deemed acceptable
        raise RouteErrors.JointRoutesNotMatchError('Trips from joint key {} do not have '.format(self.joint) +
                                                   ' matching origin and destination values.')

    def set_back_order(self):
        back_order = {}
        for key in self.order:
            back_order[self.order[key]] = key
        return back_order

    def set_display_order(self):
        # Initilize display order and first_key
        display_order = []
        cur_key = (self.routes[0].id, '0')

        # Iterate through all keys in order
        i = 0
        while i < len(self.order):
            # Convert dirnum to direction_id
            display_order.append((cur_key[0], eval('Route.objects[cur_key[0]].direction{}'.format(cur_key[1])).id))
            cur_key = self.order[cur_key]
            i += 1
        return display_order

    def set_anchor(self):
        for time in sorted(self.routes[0].time0.keys()):
            if time >= self.routes[0].start:
                return time

    def _set_schedule_anchors(self):
        """
        Set a starting time for each driver at the anchor location
        :return: True
        """
        current = self.anchor
        for driver in self.drivers:
            self.schedules[driver] = {self.routes[0].time0[current]: current}
            self._hidden_key[driver] = self.routes[0].time0[current]
            current = current + datetime.timedelta(0, 60 * int(self.headway))
        return True

    def set_schedules(self):
        self._set_schedule_anchors()

        # Forward path
        for driver in self.schedules:
            order = (self.routes[0].id, '0')
            time = self.schedules[driver][self._hidden_key[driver]]
            while True:
                # Find the time to reach the next segment
                time = time + datetime.timedelta(0, 60 * int(
                    self.trip_length[order]))
                if time > self.routes[0].end:
                    break

                # Find next trip segment
                order = self.order[order]

                # Convert time to trip id
                exec('self.schedules[driver][Route.objects[order[0]].time' +
                     '{}[time]] = time'.format(order[1]))

        # Backward path
        for driver in self.schedules:
            order = (self.routes[0].id, '0')
            time = self.schedules[driver][self._hidden_key[driver]]
            while True:
                # Find previous  trip segment
                order = self.back_order[order]

                # Find time to reach the previous segment
                time = time - datetime.timedelta(0, 60 * int(
                    self.trip_length[order]))

                try:
                    # Reset hidden key to be able to determine start values
                    self._hidden_key[driver] = eval('Route.objects[order[0]].' +
                         'time{}[time]'.format(order[1]))

                    # Convert time to trip id
                    exec('self.schedules[driver][Route.objects[order[0]].' +
                         'time{}[time]] = time'.format(order[1]))
                except KeyError:
                    break

            # Correct start location to the first StopTime of the trip
            self.locations[driver] = Trip.objects[self._hidden_key[
                driver]].stop_times[sorted(Trip.objects[self._hidden_key[
                driver]].stop_times)[0]]

    def disseminate(self):
        for driver in self.schedules:
            for trip_id in self.schedules[driver]:
                Trip.objects[trip_id].driver = driver
                for seq in Trip.objects[trip_id].stop_times:
                    StopTime.objects[(trip_id, seq)].driver = driver
                    StopTime.objects[(trip_id, seq)].joint = self.joint
        return True


class Direction(object):

    objects = {}
    convert = {}
    header_0 = 'direction_id'

    def __init__(self, id, name, description, origin, destination):
        self.id = id
        self.name = name
        self.description = description
        self.origin = origin
        self.destination = destination
        Direction.objects[id] = self
        Direction.convert[name] = id

    @classmethod
    def load(cls):
        reader = csv.reader(open(PATH + '/data/routes/direction.csv',
                            'r', newline=''), delimiter=',', quotechar='|')
        for row in reader:
            if row[0] == cls.header_0:
                continue
            cls(*row)
        return True


class Service(object):

    objects = {}
    service_dates = {}
    select_date = {}
    header_0 = 'service_id'

    def __init__(self, id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date,
                 start_time, end_time, text):
        self.id = id
        self.monday = monday
        self.tuesday = tuesday
        self.wednesday = wednesday
        self.thursday = thursday
        self.friday = friday
        self.saturday = saturday
        self.sunday = sunday
        self.start_date = datetime.datetime.strptime(start_date, '%Y%m%d')
        self.end_date = datetime.datetime.strptime(end_date, '%Y%m%d')
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.set_service_date()
        Service.objects[id] = self

    @classmethod
    def load(cls):
        reader = csv.reader(open(PATH + '/data/routes/service.csv',
                            'r', newline=''), delimiter=',', quotechar='|')
        for row in reader:
            if row[0] == cls.header_0:
                continue
            cls(*row)
        return True

    def set_service_date(self):
        if self.start_date not in Service.service_dates:
            Service.service_dates[self.start_date] = {}
        Service.service_dates[self.start_date][self.id] = True
        # If selected date in service date range add True entry to select_date
        if self.start_date <= RouteConstants.DATE <= self.end_date:
            Service.select_date[self.id] = True
        return True


class Trip(object):

    objects = {}

    def __init__(self, route_id, service_id, direction_id, trip_seq):
        self.route_id = route_id
        self.service_id = service_id
        self.direction_id = direction_id
        self.trip_seq = str(hex(trip_seq))
        self.id = '-'.join([route_id, service_id, direction_id,
                             self.trip_seq])
        self.route = Route.objects[route_id]
        self.direction = Direction.objects[direction_id]
        self.stop_times = {}
        Trip.objects[self.id] = self

    @staticmethod
    def get_trip_id(route_id, direction_id, service_id, seq):
        if '-'.join([route_id, direction_id, service_id, str(hex(seq))]
                    ) not in Trip.objects:
            Trip(route_id, direction_id, service_id, str(hex(seq)))
        return Trip.objects[(route_id, direction_id, service_id,
                             str(hex(seq)))]

    @staticmethod
    def add_stop_time(route_id, direction_id, service_id, seq, stop_id, time):
        obj = Trip.get_trip_id(route_id, direction_id, service_id,
                               str(hex(seq)))
        obj._stop_time[(stop_id, time)] = True
        return True

    def parse(self):
        return re.split('-', self.id)


class StopTime(object):

    objects = {}
    matrix_header = ['trip_id', 'stop_id', 'gps_ref', 'direction', 'arrival',
                     'departure', 'stop_seq', 'timepoint', 'pickup',
                     'dropoff', 'display', 'driver']

    def __init__(self, trip_id, stop_id, gps_ref, time, stop_seq, timepoint,
                 display):
        # Attributes from __init__
        self.trip_id = trip_id
        self.stop_id = stop_id
        self.gps_ref = gps_ref
        self.arrival = time
        self.departure = time
        self.time = time
        self.stop_seq = stop_seq
        self.timepoint = timepoint
        self.pickup = 3
        self.dropoff = 3
        self.display = display
        self.driver = 0
        self.joint = None

        # Attributes from trip_id
        self.route = Trip.objects[trip_id].route
        self.direction = Trip.objects[trip_id].direction

        # Set records
        Trip.objects[trip_id].stop_times[stop_seq] = stop_id
        StopTime.objects[(trip_id, stop_seq)] = self

    def get_record(self):
        return [self.trip_id, self.stop_id, self.gps_ref, self.direction.name,
                self.arrival, self.departure, self.stop_seq, self.timepoint,
                self.pickup, self.dropoff, self.display, self.driver]

    @staticmethod
    def publish_matrix():
        if not os.path.exists(PATH + '/reports/routes'):
            os.makedirs(PATH + '/reports/routes')
        writer = csv.writer(open(PATH +
            '/reports/routes/records' +
            '.csv', 'w', newline=''), delimiter=',', quotechar='|')
        writer.writerow(StopTime.matrix_header)
        for stop_time in StopTime.objects:
            writer.writerow(StopTime.objects[stop_time].get_record())
        return True


Route.process()
#JointRoute.process()
if __name__ == '__main__':
    StopTime.publish_matrix()
