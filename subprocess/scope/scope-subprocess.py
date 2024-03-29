from WF_SDK import device, scope, wavegen, error
import sys 
from time import sleep
import json

sig_frequency = 300e03

delimiter = '<ENDOFMESSAGE>'

def write_to_stdout(message):
    sys.stdout.write(message + delimiter)
    sys.stdout.flush()

def read_from_stdin():
    message = sys.stdin.readline().rstrip()
    json_message = json.loads(message)
    return json_message

try:
    
    device_data = device.open()
    scope.open(device_data, sampling_frequency=100e6, buffer_size=600)
    while True: 
        if device_data.name != "Digital Discovery":
            scope.trigger(device_data, enable=True, source=scope.trigger_source.analog, channel=1, level=0.01)
            # wavegen.generate(device_data, channel=1, function=wavegen.function.triangle, offset=0, frequency=sig_frequency, amplitude=2)
            buffer = scope.record(device_data, channel=1)

            time = []
            for index in range(len(buffer)):
                time.append(index * 1e06 / scope.data.sampling_frequency)   # convert time to us

            res = []
            for i in range(len(buffer)):
                res.append({'t': f'{time[i]}us', 'v': round(buffer[i], 2)})
            write_to_stdout(str(json.dumps(res)))

            sleep(0.2)

    # scope.close(device_data)
    # wavegen.close(device_data)
    # device.close(device_data)

except error as e:
    sys.stderr.write(str(e))
    sys.stderr.flush()
    device.close(device.data)
