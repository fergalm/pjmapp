from pprint import pprint
import datetime
import json

def query(iso:str) :#-> HttpResponse:

    cache = LocalCache("./cache.file")
    iso_factory = IsoFactory()

    try:
        query_obj = iso_factory.get(iso)
    except KeyError as e:
        return display_error(e)


    data = cache.get(iso, True)
    if is_stale(data):
        print("Data is stale")

        data = query_obj.query()
        cache.set(iso, data)

    return display(data)


def is_stale(data):
    then = data['datetime']
    now = datetime.datetime.now()

    # idebug()
    diff =  now - then
    if diff.total_seconds() > 3600:
        return True

    #Have we turned over the hour?
    if then.minute > now.minute:
        return True

    return False


def display(data):
    pprint(data)
    return data


def display_error(exc):
    return f"Request failed with error {type(exc)} saying {str(exc)}"

class IsoFactory:
    def __init__(self):
        self.opts = {
            'dummy': DummyIso(),
            'pjm': Pjm()
        }

    def get(self, iso:str):
        return self.opts[iso]


class AbstractIso:
    def query(self):
        raise RuntimeError("Don't call abstract class directly")

    def validate(self, res):
        assert set(res.keys()) >= set("datetime price carbon price_unit carbon_unit".split())


class DummyIso(AbstractIso):
    def __init__(self, want_stale=False):
        self.want_stale = want_stale

    def query(self):
        res = {
            'price': 12.34,
            'carbon': 98.76,
            'price_unit': 'USD',
            'carbon_unit': 'kg/MWh',
        }

        now = datetime.datetime.now()
        if self.want_stale:
            now -= datetime.timedelta(seconds=3600)
        res['datetime'] = now

        self.validate(res)
        return res

class Pjm(AbstractIso):
    def query(self):
        pass


class AbstractCache:
    def get(key, return_stale_on_error):
        pass

    def set(key, value):
        pass

    def stale_data(self, key):
        # timestamp = datetime.datetime(1970, 1,1)
        timestamp = "1970-01-01"
        return dict(datetime=timestamp, iso=key)


class LocalCache(AbstractCache):
    def __init__(self, path):
        self.path = path


    def get(self, key, return_stale_on_error=True) ->dict:
        try:
            with open(self.path, 'r') as fp:
                data = json.load(fp)
            value = data.get(key, self.stale_data(key))
        except FileNotFoundError:
            value = self.stale_data(key)

        #Convert time string to datetime object
        value['datetime'] = datetime.datetime.fromisoformat(value['datetime'])
        return value

    def set(self, key, value):

        value['datetime'] = value['datetime'].isoformat()
        try:
            with open(self.path, 'r') as fp:
                data = json.load(fp)
        except FileNotFoundError:
            #New cache file
            data = {}

        data[key] = value
        with open(self.path, 'w') as fp:
            json.dump(data, fp)

