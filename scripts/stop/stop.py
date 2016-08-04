from src.scripts.utils.classes import DataModelTemplate
from src.scripts.constants import PATH


class Stop(DataModelTemplate):

    json_path = '{}/data/stop.json'.format(PATH)
    locations = {}

    def __repr__(self):
        return '<Stop {}>'.format(self.id)

    def set_object_attrs(self):
        if self.location not in Stop.locations:
            Stop.locations[self.location] = {}
        Stop.locations[self.location][self.id[3]] = self


class Geography(DataModelTemplate):

    json_path = '{}/data/geography.json'.format(PATH)

    def __repr__(self):
        return '<Geography {}>'.format(self.id)


class Inventory(DataModelTemplate):

    json_path = '{}/data/inventory.json'.format(PATH)
    objects = {}

    def __repr__(self):
        return '<Inventory {}>'.format(self.timestamp, self.stop)

    def set_objects(self):
        Inventory.objects[(self.timestamp, self.stop)] = self
