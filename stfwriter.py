import os
import json


class STFWriter:

    def __init__(self):
        self.b = bytearray()
        self.row_count = None
        self.character_count = None
        self.fname = None

    def parse_bytes(self, value, num_bytes=None):

        if num_bytes is not None:
            x = value.to_bytes(num_bytes, 'little')
            self.b.extend(x)
        elif value <= 255:
            self.b.extend([value])
        elif (value > 255) and (value <= 65535):
            x = value.to_bytes(2, 'little')
            self.b.extend(x)
        elif (value > 65535) and (value <= 16777215):
            x = value.to_bytes(3, 'little')
            self.b.extend(x)
        elif (value > 16777215) and (value <= 335544319):
            x = value.to_bytes(4, 'little')
            self.b.extend(x)
        else:
            x = value.to_bytes(8, 'little')
            self.b.extend(x)

    def save_data(self, data, file_object):

        # [205, 171] STF file validation (ABCD)
        self.b.extend([205, 171, 0, 0, 0, 0, 0, 0, 0])

        # Row count for values
        self.row_count = len(data)
        self.parse_bytes(self.row_count, 4)
        print("Row Count for value: {}".format(self.row_count))

        # Iterate through the VALUE rows
        for i in range(self.row_count):

            # Add the row number to the byte array
            self.parse_bytes(i + 1, 4)
            self.b.extend([255, 255, 255, 255])

            # Get character count for value of each row
            self.character_count = len(data[i][1])
            self.parse_bytes(self.character_count, 4)
            # print("Character count for value: {}".format(self.character_count))

            # Iterate through characters in the row, parse their decimal values, and add an empty byte
            for i in data[i][1]:
                self.parse_bytes(ord(i))
                self.b.extend([0])

        # Iterate through KEY rows
        for i in range(self.row_count):

            # Add the row number to the byte array
            self.parse_bytes(i + 1, 4)

            # Get character count for key of each row
            self.character_count = len(data[i][0])
            self.parse_bytes(self.character_count, 4)
            # print("Character count for key: {}".format(self.character_count))

            # Iterate through characters in the row and parse their decimal values
            for i in data[i][0]:
                self.parse_bytes(ord(i))

        # print(self.b)

        file_object.write(self.b)
