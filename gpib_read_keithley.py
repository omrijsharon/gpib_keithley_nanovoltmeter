import pyvisa
from time import sleep

def parse_reading(reading):
    prefix = reading[:4]
    rest = reading[4:].split(',')
    value = float(rest[0].replace('E', 'e'))
    buffer_location = int(rest[1])
    timestamp = float(rest[2])
    return prefix, value, buffer_location, timestamp


# enum of the possible ranges, from 3mV to 30V, starting with auto-range and ending with disable auto-range.
class VoltageRange:
    AUTO = 0
    RANGE_3MV = 1
    RANGE_30MV = 2
    RANGE_300MV = 3
    RANGE_3V = 4
    RANGE_30V = 5
    NO_FUNCTION = 6
    NO_FUNCTION_2 = 7
    DISABLE_AUTO = 8


# Class to interface with the Keithley 182
class Keithley182:
    def __init__(self, inst=None):
        if inst is not None:
            self._inst = inst
        else:
            self._inst = self.find_instrument()
        if self._inst is None:
            raise Exception("No Keithley 182 found")
        self._inst.timeout = 2000
        self._inst.write_termination = ''
        self._inst.read_termination = ''
        self.trigger_interval = 1000
        self.set_trigger_interval(self.trigger_interval)
        self._inst.write(f'G7X') # Reading, with prefix and timestamp

    def manual_trigger(self):
        self._inst.write('H0X')

    def set_circular_buffer(self):
        self._inst.write('I2X')

    def set_linear_buffer(self, length):
        # length must be an integer
        assert isinstance(length, int), "Buffer length must be an integer"
        assert 1 <= length <= 1024, "Invalid buffer length"
        self._inst.write(f'I1,{length}X')

    def find_instrument(self):
        rm = pyvisa.ResourceManager(r"C:\Windows\system32\visa64.dll")
        resources = rm.list_resources()

        for name in resources:
            if 'GPIB' in name:
                print(f"Opening {name}")
                inst = rm.open_resource(name)
                return inst
        return None

    def set_range(self, range):
        '''
        :param range: The range to set the Keithley 182 to. Must be a value from the VoltageRange enum.
        :usage: keithley.set_range(VoltageRange.AUTO)
        '''
        assert 0 <= range <= 8, "Invalid range"
        self._inst.write(f'R{range}X')

    def read_single(self):
        return parse_reading(self._inst.query('F0X'))

    def read_from_buffer(self):
        self.manual_trigger()
        print(self._inst.write('F2X'))
        for i in range(10):
            # sleep(self.trigger_interval / 1000)
            self.manual_trigger()
            print(self._inst.read())

    def set_trigger_interval(self, interval_ms):
        # format is Q<time in ms>X
        # interval_ms must be an integer between 10 and 999,999
        assert isinstance(interval_ms, int), "Interval must be an integer"
        assert 10 <= interval_ms <= 999999, "Invalid interval"
        self.trigger_interval = interval_ms
        self._inst.write(f'Q{interval_ms}X')

    def __call__(self, query):
        return self._inst.query(query)

    def close(self):
        self._inst.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    nanovoltmeter = Keithley182()
    # nanovoltmeter.set_range(VoltageRange.RANGE_3V)
    nanovoltmeter.manual_trigger()
    print(nanovoltmeter.read_single())
    nanovoltmeter.set_linear_buffer(8)
    nanovoltmeter.set_trigger_interval(1234)
    print(nanovoltmeter('U9X'))
    # nanovoltmeter.read_from_buffer()
