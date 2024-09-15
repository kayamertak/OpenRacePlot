import os
import struct
import crcmod
import csv
from typing import List, Dict, Optional

class MoTeCParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.crc32_func = crcmod.predefined.mkCrcFun('crc-32')
        self.data = []

    def read_file(self) -> bytes:
        with open(self.file_path, 'rb') as file:
            raw_data = file.read()
        print(f"Raw data read from file: {raw_data[:100]}...")  # Added print statement
        return raw_data

    def parse_data(self, raw_data: bytes) -> List[Dict[str, float]]:
        index = 0
        data_length = len(raw_data)
        temp_data = []
        parsed_data = []

        while index < data_length:
            msg = raw_data[index:index + 8]
            print(f"Processing message at index {index}: {msg}")  # Debug message for each segment
            if not msg:
                break
            temp_data.append(msg)
            if self.is_message_start(temp_data):
                print(f"Message start detected at index {index}")  # Debug when message start is detected
                if self.crc_check(temp_data):
                    print(f"CRC check passed at index {index}")  # Debug when CRC check passes
                    parsed_row = self.extract_data(temp_data)
                    if parsed_row:
                        print(f"Parsed row: {parsed_row}")  # Debug parsed row data
                        parsed_data.append(parsed_row)
                    temp_data.clear()
            index += 8
        return parsed_data

    def extract_data(self, can_data: List[bytes]) -> Dict[str, float]:
        try:
            extracted_data = {
                'rpm': struct.unpack('>H', can_data[0][4:6])[0],
                'tps': struct.unpack('>H', can_data[0][6:8])[0] * 0.1,
                'manifold pressure': struct.unpack('>H', can_data[1][0:2])[0] * 0.1,
                'air temp': struct.unpack('>H', can_data[1][2:4])[0] * 0.1,
                'engine temp': struct.unpack('>H', can_data[1][4:6])[0] * 0.1,
                'lambda1': struct.unpack('>H', can_data[1][6:8])[0] * 0.001,
                'lambda2': struct.unpack('>H', can_data[2][0:2])[0] * 0.001,
                'exhaust manifold pressure': struct.unpack('>H', can_data[2][2:4])[0] * 0.1,
                'mass air flow': struct.unpack('>H', can_data[2][4:6])[0] * 0.1,
                'fuel temp': struct.unpack('>H', can_data[2][6:8])[0] * 0.1,
                'fuel pressure': struct.unpack('>H', can_data[3][0:2])[0] * 0.1,
                'oil temp': struct.unpack('>H', can_data[3][2:4])[0] * 0.1,
                'oil pressure': struct.unpack('>H', can_data[3][4:6])[0] * 0.1,
                'gear voltage': struct.unpack('>H', can_data[3][6:8])[0] * 0.01,
                'knock voltage': struct.unpack('>H', can_data[4][0:2])[0] * 0.1,
                'gear shift force': struct.unpack('>H', can_data[4][2:4])[0] * 0.1,
                'exhaust temp1': struct.unpack('>H', can_data[4][4:6])[0],
                'exhaust temp2': struct.unpack('>H', can_data[4][6:8])[0],
                'user channel1': struct.unpack('>H', can_data[5][0:2])[0] * 0.1,
                'user channel2': struct.unpack('>H', can_data[5][2:4])[0] * 0.1,
                'user channel3': struct.unpack('>H', can_data[5][4:6])[0] * 0.1,
                'user channel4': struct.unpack('>H', can_data[5][6:8])[0] * 0.1,
                'battery voltage': struct.unpack('>H', can_data[6][0:2])[0] * 0.01,
                'ecu temp': struct.unpack('>H', can_data[6][2:4])[0] * 0.1,
                'digital input1 speed': struct.unpack('>H', can_data[6][4:6])[0] * 0.1,
                'digital input2 speed': struct.unpack('>H', can_data[6][6:8])[0] * 0.1,
                'digital input3 speed': struct.unpack('>H', can_data[7][0:2])[0] * 0.1,
                'digital input4 speed': struct.unpack('>H', can_data[7][2:4])[0] * 0.1,
                'drive speed': struct.unpack('>H', can_data[7][4:6])[0] * 0.1,
                'ground speed': struct.unpack('>H', can_data[7][6:8])[0] * 0.1,
                'slip': struct.unpack('>H', can_data[8][0:2])[0] * 0.1,
                'aim slip': struct.unpack('>H', can_data[8][2:4])[0] * 0.1,
                'launch rpm': struct.unpack('>H', can_data[8][4:6])[0] * 0.1,
                'gear': struct.unpack('>H', can_data[14][4:6])[0],
                'low battery': can_data[16][7] & 1,
                'no sync': can_data[16][7] & 4,
                'sync': can_data[16][6] & 8,
                'no ref': can_data[16][6] & 16,
                'ref': can_data[16][6] & 32,
                'rpm over': can_data[16][6] & 64
            }
            print(f"Extracted data: {extracted_data}")  # Add this line to print extracted data
            return extracted_data
        except (IndexError, AttributeError, KeyError) as e:
            print(f"Error extracting data: {e}")
            return {}

    def is_message_start(self, temp_data: List[bytes]) -> bool:
        try:
            start_detected = temp_data[0][0] == 130 and temp_data[0][1] == 129 and temp_data[0][2] == 128 and temp_data[0][3] == 84
            print(f"Message start detected: {start_detected}, Data: {temp_data[0]}")  # Print the status of message start detection
            return start_detected
        except IndexError:
            return False

    def crc_check(self, temp_data: List[bytes]) -> bool:
        try:
            dataval = bytearray()
            for i in range(21):
                dataval.extend(temp_data[i])
            dataval.extend(temp_data[21][:4])

            crc = hex(self.crc32_func(dataval))
            splitdataval = [crc[i:i + 2] for i in range(0, len(crc), 2)]

            for i in range(4):
                if hex(int(splitdataval[i + 1], 16)) != hex(temp_data[21][i + 4]):
                    print(f"CRC mismatch: calculated {hex(int(splitdataval[i + 1], 16))}, received {hex(temp_data[21][i + 4])}")  # Print CRC check failures
                    return False

            return True

        except (IndexError, AttributeError) as e:
            print(f"CRC check failed: {e}")
            return False

class MoTeCCsvWriter:
    def __init__(self, output_file: str, channels: Optional[List[str]] = None):
        self.output_file = output_file
        self.channels = channels or [
            'rpm', 'tps', 'manifold pressure', 'air temp', 'engine temp',
            'lambda1', 'lambda2', 'exhaust manifold pressure', 'mass air flow',
            'fuel temp', 'fuel pressure', 'oil temp', 'oil pressure', 'gear voltage',
            'knock voltage', 'gear shift force', 'exhaust temp1', 'exhaust temp2',
            'user channel1', 'user channel2', 'user channel3', 'user channel4',
            'battery voltage', 'ecu temp', 'digital input1 speed', 'digital input2 speed',
            'digital input3 speed', 'digital input4 speed', 'drive speed', 'ground speed',
            'slip', 'aim slip', 'launch rpm', 'gear', 'low battery', 'no sync', 'sync',
            'no ref', 'ref', 'rpm over'
        ]

    def write_csv(self, data: List[Dict[str, float]]):
        with open(self.output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.channels)
            writer.writeheader()
            for row in data:
                if row:  # Ensure row is not None or empty
                    print(f"Writing row to CSV: {row}")
                    writer.writerow(row)
                else:
                    print("Skipped empty or None row.")

class MoTeCConverter:
    def __init__(self, parser: MoTeCParser, writer: MoTeCCsvWriter):
        self.parser = parser
        self.writer = writer

    def convert(self):
        raw_data = self.parser.read_file()
        parsed_data = self.parser.parse_data(raw_data)
        if parsed_data:
            print(f"Parsed data (first 5 entries): {parsed_data[:5]}")  # Print a sample of parsed data
        else:
            print("No valid data parsed.")
        self.writer.write_csv(parsed_data)
        print(f"Conversion complete! CSV file saved to {self.writer.output_file}")


if __name__ == "__main__":
    # Specify the input and output file paths
    input_file_path = "C:/Users/mcwar/Desktop/Kaya/Data_Vis_Software/Sample.ld"
    output_file_path = "C:/Users/mcwar/Desktop/Kaya/Data_Vis_Software/Converted_data.csv"

    # Create instances of the parser and writer
    parser = MoTeCParser(input_file_path)
    writer = MoTeCCsvWriter(output_file_path)

    # Create the converter and perform the conversion
    converter = MoTeCConverter(parser, writer)
    converter.convert()
