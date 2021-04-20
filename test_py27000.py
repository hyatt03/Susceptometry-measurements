import time
import py2700 as DMM

# Connect to a Keithley 2701 over TCP/IP
my_multimeter = DMM.Multimeter('ASRL6::INSTR')

# Set the timeout in ms
my_multimeter.set_timeout(15000)

# Set Channels 101, 102, and 103 as K-type thermocouples
my_multimeter.define_channels([101,102,103],
    DMM.MeasurementType.resistance())

# Setup for reading:
#   This needs to be completed after channel
#   definitions and before scanning
my_multimeter.setup_scan()

# Scan the channels, given the timestamp you want
# for the reading
result = my_multimeter.scan(time.time_ns()/(10**9))

# Print out a CSV header for the result
print(my_multimeter.make_csv_header())

# Print out a CSV row for the result
print(result.make_csv_row())

# Safely disconnect from the multimeter
my_multimeter.disconnect()