import re
import glob
import os
import io
import numpy as np
import json
import csv
import json
import stfwriter

file = "/home/almin/Workspace/convotemp/test1.stf"


class STFReader:
    def __init__(self):
        self.buffer = None
        self.value_array = {}
        self.key_array = {}
        self.char = ""

    def read_byte(self, num_bytes):
        buffer = self.buffer.read(num_bytes)

        dt = np.dtype(np.int32)
        dt = dt.newbyteorder('<')
        bytes = np.frombuffer(buffer, dtype=dt)
        return bytes

    def read_stf(self, file_data):
        self.buffer = io.BytesIO(file_data)
        self.buffer.read(9)
        row_count = self.read_byte(4)

        for i in range(row_count[0]):
            row_number = self.read_byte(4)
            self.read_byte(4)
            character_count = self.read_byte(4)

            for i in range(character_count[0]):
                character = chr(self.buffer.read(2)[0])
                self.char = self.char + character
                self.value_array[row_number[0]] = self.char

            self.char = ""

        for i in range(row_count[0]):
            row_number = self.read_byte(4)
            character_count = self.read_byte(4)

            for i in range(character_count[0]):
                character = chr(self.buffer.read(1)[0])
                self.char = self.char + character
                self.key_array[row_number[0]] = self.char

            self.char = ""

        data = {}
        convo_string = []
        data_dict = {}

        for i in range(row_count[0]):
            value = ""
            try:
                key = self.key_array[i + 1]
                value = self.value_array[i + 1]
                data[i] = [key, value]
                data_dict[i] = value
                convo_string.append(value)
            except:
                data[i] = [key, value]
            pass
        return data_dict


reader = STFReader()


with open(file, 'rb') as file:
    content = file.read()
    data = reader.read_stf(content)
    for k, v in data.items():
        data[k] = v.replace('\n', '')

with open('file.json', 'w') as jfile:
    json_object = json.dumps(data, indent=4)
    json.dump(data, jfile, indent=4)
