#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

# Python libraries and packages
import copy
import datetime
import math
import re
import sys

# Import GO scripts
from src.scripts.constants import *
from src.scripts.stop.stop import Stop
from src.scripts.route.errors import *
from src.scripts.route.segment import Segment, StopSeq, load_segments
from src.scripts.route.service import Service
from src.scripts.route.trip import Trip, StopTime
from src.scripts.utils.classes import DataModelTemplate
from src.scripts.utils.functions import stitch_dicts
from src.scripts.utils.send_requests import DataRequest


CREATE_NEW_FEED = True  # Toggle to True if you wish to download the current route planning and produce new outputs


class Route:

    route_query = {}
    loc_to_stop = {}

    @staticmethod
    def set_route_query():

        for obj in Schedule.objects:
            schedule = Schedule.objects[obj]

            for dir_order in schedule.segments:
                segment = schedule.segments[dir_order]

                if segment.route not in Route.route_query:
                    Route.route_query[segment.route] = {}

                start = schedule.joint.service.start_date
                end = schedule.joint.service.end_date

                if (start, end) not in Route.route_query[segment.route]:
                    Route.route_query[segment.route][(start, end)] = {}

                for stop in segment.stops:
                    # It is important to remove the GPS_REF
                    Route.route_query[segment.route][(start, end)][stop[:3]] = True

        return True

    @staticmethod
    def query_route(route, date, stop):
        if route in Route.route_query:
            for key in Route.route_query[route]:
                if key[0] <= date <= key[1]:
                    if stop in Route.route_query[route][key]:
                        return True
        return False

    @staticmethod
    def convert_locs_to_stops(joint, on, off):

        # Find all potential on and off stops by shared location value
        min_length = (sys.maxsize, 0, 0)
        for schedule in joint.schedules:
            on_map = []
            off_map = []

            for dir_order in schedule.segments:
                segment = schedule.segments[dir_order]
                if on in segment.locs:
                    on_map += segment.locs[on]
                if off in segment.locs:
                    off_map += segment.locs[off]

            # Find the minimum trip distance between on and off stop_seqs
            for on_stop in on_map:
                for off_stop in off_map:
                    trip_length = schedule.get_trip_length(on_stop, off_stop)
                    if trip_length < min_length[0]:
                        min_length = (trip_length, on_stop.stop, off_stop.stop)

        return min_length[1:]


class Joint(DataModelTemplate):

    objects = {}
    json_path = '{}/route/joint.json'.format(DATA_PATH)
    locations = {}

    def set_object_attrs(self):
        self.service = Service.objects[self.service]
        self.schedules = {}

    def __repr__(self):
        return '<Joint {}>'.format(self.id)

    @staticmethod
    def process():
        ranges = {}
        for obj in Joint.objects:
            joint = Joint.objects[obj]
            # Create trips for each schedule in order
            prev = None
            for schedule in joint.sort_schedules():
                schedule.prev = schedule.check_prev(prev)
                schedule.drivers = Driver.get_drivers(math.ceil(schedule.roundtrip / joint.headway), schedule.id
                                                      ) if not prev else Driver.add_schedule(prev.drivers, schedule.id)
                schedule.set_trips()
                prev = schedule

            date_key = (joint.service.start_date, joint.service.end_date + datetime.timedelta(days=1))
            if date_key not in ranges:
                ranges[date_key] = []
            ranges[date_key] = ranges.get(date_key) + [joint]

        DateRange.set_ranges(ranges)
        return True

    def get_json(self):
        attrs = dict([(k, getattr(self, k)) for k in ['id', 'desc', 'routes', 'headway']])
        attrs['service'] = self.service.id
        return attrs

    def sort_schedules(self):
        sorted_schedules = {}
        for schedule in self.schedules:
            sorted_schedules[schedule.start] = schedule
        return [sorted_schedules[key] for key in sorted(sorted_schedules.keys())]


class Schedule(DataModelTemplate):

    objects = {}
    json_path = '{}/route/schedule.json'.format(DATA_PATH)

    def set_object_attrs(self):
        self.joint = Joint.objects[self.joint]
        self.start_str = self.start
        self.end_str = self.end
        self.segments = SegmentOrder.lookup[self.id]

        # Set times
        hour, minute, second = [int(i) for i in re.split(':', self.start)]
        self.start = copy.deepcopy(self.joint.service.start_date).replace(hour=hour, minute=minute, second=second)
        hour, minute, second = [int(i) for i in re.split(':', self.end)]
        self.end = copy.deepcopy(self.joint.service.start_date).replace(hour=hour, minute=minute, second=second)

        # Handle end times that are at or after midnight (24+ hour scale for GTFS) by incrementing the day
        if self.end < self.start:
            self.end = self.end + datetime.timedelta(days=1)

        self.drivers = {}
        self.prev = None
        self.roundtrip = self.get_roundtrip()
        self.order = self.get_order()
        self.joint.schedules[self] = True
        self.end_locs = {}

    def __repr__(self):
        return '<Schedule {}>'.format(self.id)

    def __str__(self):
        return '<Schedule {}>'.format(self.id)

    def __lt__(self, other):
        return (self.start, self.end) < (other.start, other.end)

    def __le__(self, other):
        return (self.start, self.end) <= (other.start, other.end)

    def __eq__(self, other):
        return (self.start, self.end) == (other.start, other.end)

    def __ne__(self, other):
        return (self.start, self.end) != (other.start, other.end)

    def __gt__(self, other):
        return (self.start, self.end) > (other.start, other.end)

    def __ge__(self, other):
        return (self.start, self.end) >= (other.start, other.end)

    def __hash__(self):
        return hash((self.start, self.end))

    def check_prev(self, prev):
        if prev:
            # If the number of driver shifts between this and the previous schedule do not match
            if len(prev.drivers) != math.ceil(self.roundtrip / self.joint.headway):
                # Raise an error because they should match
                raise JointRouteMismatchedDriverCount('JointRoute {} has mismatched driver counts for {} and {}'.format(
                    self.joint.id, prev.id, self.id))

        return prev

    def get_roundtrip(self):
        # Find joint roundtrip for current time schedule
        roundtrip = 0
        for segment in self.segments:
            roundtrip += self.segments[segment].trip_length
        return roundtrip

    def get_order(self):
        order = {}  # {<Segment>: next_<Segment>}
        for segment in self.segments:
            # Segment_key represents the next segment, which is dir_order + 1 or if the final dir_order the next is 0
            segment_key = segment + 1 if segment + 1 in self.segments else 0
            # Set dir_order as key and value
            # order[segment] = segment_key
            # Set Segment object as key and value
            order[self.segments[segment]] = self.segments[segment_key]
        return order

    def get_trip_length(self, a, b):
        """
        :param a: The origin of the trip; MUST be a Segment OR a
            StopSeq object
        :param b: The destination of the trip; MUST be a Segment OR a
            StopSeq object
        :return: The trip length
        """
        trip_length = 0

        # If the origin is a StopSeq subtract the departure time from the trip_length
        if re.search('stopseq', str(a.__class__).lower()):
            trip_length -= a.depart
            a = a.segment

        # If the destination is a StopSeq add the departure time to the trip_length
        if re.search('stopseq', str(b.__class__).lower()):
            trip_length += b.depart
            b = b.segment

        # Continue traveling the order until the cur_segment and final_segment are the same
        while a != b:
            # Add current segment's trip_length to the total trip_length
            trip_length += a.trip_length
            # Shift the cur_segment forward
            a = self.order[a]

        return trip_length % self.roundtrip

    def get_segment_loc(self, loc):
        """
        Input is the absolute schedule location and the result is the
        relative segment location along with the Segment object
        :param loc: absolute schedule location
        :return: (Segment, relative_location)
        """
        loc %= self.roundtrip
        distance = 0
        segment = self.segments[0]
        while (distance + segment.trip_length) < loc:
            distance += segment.trip_length
            segment = self.order[segment]
        return segment, loc - distance

    def get_schedule_loc(self, segment, loc):
        """
        Input is the relative segment location and the result is the
        absolute schedule location
        :param segment: Segment object of the current location
        :param loc: relative segment location
        :return: (Segment, relative_location)
        """
        distance = -loc
        while segment != self.segments[0]:
            distance += segment.trip_length
            segment = self.order[segment]
        return (self.roundtrip - distance) % self.roundtrip

    def get_start_locs(self):
        """
        Find all of the driver starting locations; remember location is
        time from the origin and not a physical location
        :return: {start_loc: driver}
        """
        start_locs = {}
        last = self.offset  # starting position is equal to the schedule's offset
        d = 0  # index of the current driver position

        while d < len(self.drivers):
            start_locs[last] = self.drivers[d]
            # Increment the last location distance by the headway % the roundtrip in case the origin is passed
            last = (last + self.joint.headway) % self.roundtrip
            d += 1

        # If prev return stitched dictionary
        if self.prev:
            return self.stitch_prev(start_locs)

        # Otherwise return start_locs as-is
        return start_locs

    def stitch_prev(self, start_locs):
        # Stitch prev and current drivers together
        stitch = stitch_dicts(self.prev.end_locs, start_locs)

        # Check for errors
        if stitch == 'Sizes incongruent problem':
            raise IncongruentSchedulesError('Joint route {} has schedules that are incongruent:'.format(self.joint) +
                                            ' {} and {}'.format(self.prev.id, self.id))

        elif stitch == 'Duplicate problem':
            raise MismatchedJointSchedulesTimingError('Joint route {} has schedules with '.format(self.joint) +
                                                      'mismatched timing likely to do significant differences in ' +
                                                      'route design: {} {}'.format(self.prev.id, self.id))

        elif stitch == 'Lax problem':
            raise LaxConstraintFailureError('Joint route {} has schedules that violate the LAX '.format(self.joint) +
                                            'constraint: {} {}'.format(self.prev.id, self.id))

        return stitch

    def generate_trips(self, loc, driver):
        segment, start_loc = self.get_segment_loc(loc)
        end_loc = start_loc
        start = copy.deepcopy(self.start)
        end = copy.deepcopy(self.end)
        while start < end:

            # Calculate end_loc
            # Find the end time which is the start time + Segment.trip_length - start_loc time
            trip_end = start + datetime.timedelta(seconds=(segment.trip_length-start_loc))
            if trip_end > end:
                end_loc = start_loc + (end - start).total_seconds()
            else:
                end_loc = segment.trip_length

            # Set trip
            Trip(**{
                'id': '-'.join(str(s) for s in [self.joint.id, self.id, segment.id, segment.trip_generator]),
                'schedule': self.id,
                'route': segment.route,
                'service': self.joint.service.id,
                'segment': segment.id,
                'head_sign': 'to {}'.format(segment.direction),
                'direction': segment.dir_type_num,
                'start_loc': start_loc,
                'end_loc': end_loc,
                'start_time': start.strftime('%Y-%m-%d %H:%M:%S'),
                'driver': driver
            }).create_stop_times(segment.query_stop_seqs(start_loc, end_loc), self.joint.service)
            segment.trip_generator += 1

            # Set driver start location -- SHOULD THIS ONLY APPLY IF START NOT EXISTING? OTHERWISE OVERWRITING?
            driver.start = segment.query_min_stop_seq(start_loc, end_loc)

            # Calculate next start
            start_loc = 0
            start = trip_end
            segment = self.order[segment] if trip_end < end else segment
            end_loc = 0 if trip_end == end else end_loc

        # Set self.end_locs
        self.end_locs[self.get_schedule_loc(segment, end_loc)] = driver

    def set_trips(self):
        start_locs = self.get_start_locs()

        # Iterate through each driver and set their trips
        for loc in start_locs:
            self.generate_trips(loc, start_locs[loc])

        # Take min loc from origin and add key of loc + roundtrip to create the idea of a circular graph
        self.end_locs[min(self.end_locs) + self.roundtrip] = self.end_locs[min(self.end_locs)]


class SegmentOrder(DataModelTemplate):

    json_path = '{}/route/segment_order.json'.format(DATA_PATH)
    lookup = {}

    def set_object_attrs(self):
        self.segment = Segment.objects[self.segment]
        self.segment.dir_type_num = 1 if self.dir_type == 'inbound' or self.dir_type == 'I' else 0
        if self.schedule not in SegmentOrder.lookup:
            SegmentOrder.lookup[self.schedule] = {}
        SegmentOrder.lookup[self.schedule][self.order] = self.segment

    def set_objects(self):
        pass


class DateRange(DataModelTemplate):

    json_path = '{}/route/date_range.json'.format(DATA_PATH)
    objects = {}

    def set_object_attrs(self):
        self.start = datetime.datetime.strptime(self.start, '%Y-%m-%d')
        self.end = datetime.datetime.strptime(self.end, '%Y-%m-%d')
        self.joints = [Joint.objects[joint] for joint in self.joints]

    def set_objects(self):
        DateRange.objects[(self.start, self.end)] = self

    def __repr__(self):
        return '<DateRange {}-{}>'.format(self.start, self.end)

    @staticmethod
    def set_ranges(ranges):
        """
        Build non-overlapping DateRange objects populated with all
        joint routes within the DateRange object's start and end date.
        :param ranges: {(start, end): [Joint, Joint, ... ]}
        :return: True after setting up DateRange objects with joints
        """
        # Find all unique start and end dates
        points = {}
        for date_range in ranges:
            for date in date_range:
                points[date] = True
        points = sorted(list(points.keys()))

        # Order the dates and create ranges between each two ordered points
        i = 0
        while i < len(points) - 1:
            DateRange(**{
                'start': points[i].strftime('%Y-%m-%d'),
                'end': points[i+1].strftime('%Y-%m-%d'),
                'joints': [],
                'lookup': {}
            })
            i += 1

        # Connect Joint objects to DateRange objects
        for date_range in ranges:
            for obj in DateRange.objects:
                if date_range[0] <= DateRange.objects[obj].start and date_range[1] >= DateRange.objects[obj].end:
                    DateRange.objects[obj].joints += ranges[date_range]

        # Set position for all date ranges
        for obj in DateRange.objects:
            DateRange.objects[obj].set_positions()

    def set_positions(self):
        self.joints = [Joint.objects[joint] for joint in sorted([joint.id for joint in self.joints])]

        # Set driver positions and collect trips
        position = 1
        for joint in self.joints:
            for schedule in joint.schedules:
                for driver in sorted(schedule.drivers.keys()):
                    # Set the driver's position if schedule has not been seen
                    if not schedule.prev:
                        self.lookup[schedule.drivers[driver].id] = position
                        position += 1
        return True

    @staticmethod
    def get_obj_by_date(date):
        for obj in DateRange.objects:
            date_range = DateRange.objects[obj]
            if date_range.start <= date < date_range.end:
                return date_range

    def get_default_feed(self):
        return self.get_feed(cls='Trip'), self.get_feed(cls='StopTime')

    def get_feed(self, cls='Trip'):
        container = {}
        for joint in self.joints:
            for schedule in joint.schedules:
                container.update(eval('{}.feed[{}]'.format(cls, schedule.id)))
        return container

    def get_json(self):
        return {
            'start': self.start.strftime('%Y-%m-%d'),
            'end': self.end.strftime('%Y-%m-%d'),
            'joints': [joint.id for joint in self.joints],
            'lookup': self.lookup
        }


class Driver(DataModelTemplate):

    json_path = '{}/route/route_driver.json'.format(DATA_PATH)
    objects = {}
    gen_unique_id = 1

    def __repr__(self):
        return 'Driver {} for schedules {}'.format(self.id, ', '.join([str(s) for s in self.schedules]))

    @classmethod
    def get_drivers(cls, n, schedule):
        Driver.gen_unique_id += n
        return dict([(x - (Driver.gen_unique_id - n), cls(**{
            'id': x,
            'start': None,
            'schedules': [schedule]
        })) for x in range(Driver.gen_unique_id - n, Driver.gen_unique_id)])

    @classmethod
    def add_schedule(cls, drivers, schedule):
        for segment_order in drivers:
            drivers[segment_order].schedules += [schedule]
        return drivers


def create(date=datetime.datetime.today()):
    # Retrieve data from database first
    DataRequest('agency', '/agency/agency.json').get()
    DataRequest('holiday', '/route/holiday.json').get()
    DataRequest('joint', '/route/joint.json').get()
    DataRequest('route', '/route/route.json').get()
    DataRequest('schedule', '/route/schedule.json').get()
    DataRequest('segment', '/route/segment.json').get()
    DataRequest('segment_order', '/route/segment_order.json').get()
    DataRequest('service', '/route/service.json').get()
    DataRequest('stop', '/stop/stop.json').get()
    DataRequest('stop_seq', '/route/stop_seq.json').get()

    # Load dependent data
    Stop.load()
    load_segments()
    Service.load()

    # Then process by loading the obtained data
    Joint.load()
    SegmentOrder.load()
    Schedule.load()
    Joint.process()
    Route.set_route_query()
    StopTime.publish_matrix()
    Driver.export()
    Trip.export()
    StopTime.export()
    feed = DateRange.get_obj_by_date(date).get_default_feed()
    DateRange.export()
    return feed


def load(date=datetime.datetime.today()):
    Stop.load()
    load_segments()
    Service.load()
    Joint.load()
    SegmentOrder.load()
    Schedule.load()
    DateRange.load()
    Driver.load()
    Trip.load()
    StopTime.load()
    Route.set_route_query()
    return DateRange.get_obj_by_date(date).get_default_feed()


if __name__ == "__main__":
    feed = create() if CREATE_NEW_FEED else load()
