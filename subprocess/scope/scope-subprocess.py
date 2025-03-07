from WF_SDK import device, scope, wavegen, error, logic
import sys 
from time import sleep
import json
import select

sig_frequency = 300e03

delimiter = '<ENDOFMESSAGE>'

def write_to_stdout(message):
    sys.stdout.write(message + delimiter)
    sys.stdout.flush()

def read_from_stdin():
    message = sys.stdin.readline().rstrip()
    json_message = json.loads(message)
    return json_message

last_input_voltage = 0

try:
    
    device_data = device.open()
    scope.open(device_data, sampling_frequency=100e6, buffer_size=600)
    logic.open(device_data, buffer_size=600)
    logic.trigger(device_data, enable=True, channel=0, rising_edge=True, timeout=0.2)
    while True: 
        if device_data.name != "Digital Discovery":
            user_inputs = [] 
            while True: 
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]: 
                    try: user_inputs.append(input()) 
                    except EOFError: break 
                else: break
            if (len(user_inputs) > 0):
                last_input_voltage = float(user_inputs[-1])
            if last_input_voltage > 2.5:
                scope.open(device_data, sampling_frequency=100e6, buffer_size=600, amplitude_range=20)
            else:
                scope.open(device_data, sampling_frequency=100e6, buffer_size=600)
            #scope.open(device_data, sampling_frequency=100e6, buffer_size=600, amplitude_range=last_input_voltage)
            scope.trigger(device_data, enable=True, source=scope.trigger_source.digital, channel=0, edge_rising=True, timeout=0.2)
            #wavegen.generate(device_data, channel=1, function=wavegen.function.triangle, offset=0, frequency=sig_frequency, amplitude=2)
            buffer_voltage = scope.record(device_data, channel=1)
            #scope.trigger(device_data, enable=True, source=scope.trigger_source.digital, channel=0, edge_rising=True, timeout=0.1)
            buffer_current = scope.record(device_data, channel=2)
            buffer_pwm = logic.record(device_data, channel=0)

            time = []
            for index in range(len(buffer_voltage)):
                time.append(index * 1e06 / scope.data.sampling_frequency)   # convert time to us

            for i in range(len(buffer_current)):
                buffer_current[i] = (buffer_current[i] - 0.65) * 10 # Amperes

            write_to_stdout(str(json.dumps({"voltage": buffer_voltage, "time": time, "pwm": buffer_pwm, "current": buffer_current})))

            sleep(0.2)

    # scope.close(device_data)
    # wavegen.close(device_data)
    # device.close(device_data)

except error as e:
    sys.stderr.write(str(e))
    sys.stderr.flush()
    device.close(device.data)