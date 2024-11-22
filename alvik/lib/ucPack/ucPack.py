import struct

from ucPack.CircularBuffer import CircularBuffer


class ucPack:

    def __init__(self, buffer_size: int, start_index: int = ord('A'), end_index: int = ord('#')):
        self.buffer_size = buffer_size
        self.buffer = CircularBuffer(buffer_size)
        self.start_index = start_index
        self.end_index = end_index

        self.payload = bytearray(buffer_size)

        self.msg = bytearray(buffer_size)
        self.msg_size = 0

    def checkPayload(self) -> bool:
        """
        Parses and checks the buffer to get the payload
        :return:
        """

        # check if buffer is empty
        if self.buffer.isEmpty():
            return False

        # check the index byte
        while not (self.buffer.top() == self.start_index) and (self.buffer.getSize() > 0):
            self.buffer.pop()

        # exit if only message index is received
        if self.buffer.getSize() <= 1:
            return False

        # get the payload dimension
        payload_size = self.buffer[1]

        # check if packet is complete
        if self.buffer.getSize() < (payload_size + 4):     # memo: index|length|msg|stop|crc8
            return False

        # check if stop byte is correct
        if self.buffer[payload_size + 2] != self.end_index:
            return False

        # crc checking
        for i in range(0, payload_size):
            self.payload[i] = self.buffer[i + 2]

        if self.crc8(self.payload[0:payload_size]) != self.buffer[payload_size + 3]:
            self.buffer.pop()   # delete the index so it is possible to recheck
            return False

        # clear the buffer
        for _ in range(0, payload_size + 4):
            self.buffer.pop()

        return True

    @staticmethod
    def crc8(data: [int]) -> int:
        """
        Calculates the CRC8-MAXIM of the data array
        :param data: the input data array
        :return: the calculated crc
        """

        crc = 0x00

        for extract in data:
            for _ in range(0, 8):
                sum = (crc ^ extract) & 0x01
                crc = crc >> 1
                if sum:
                    crc = crc ^ 0x8C
                extract = extract >> 1

        return crc

    def payloadTop(self):
        """
        Returns the top element of the payload array
        :return:
        """

        return self.payload[0]

    def packetC1B(self, code: int, b: int) -> int:
        """
        Packets the byte b with command code + start and end indexes
        :param code:
        :param b: the 'byte' to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 2
        self.msg[2] = code & 0xFF
        self.msg[3] = b & 0xFF
        self.msg[4] = self.end_index & 0xFF
        self.msg[5] = self.crc8(self.msg[2:4])
        self.msg_size = 6
        return self.msg_size

    def unpacketC1B(self) -> (int, int):
        """
        Unpackets the payload expecting a command code and one byte
        :return: code and byte
        """

        code = self.payload[0]
        b = self.payload[1]
        return code, b

    def packetC2B(self, code: int, b1: int, b2: int) -> int:
        """
        Packets bytes b1 and b2 with command code + start and end indexes
        :param code:
        :param b1: first 'byte' to packet
        :param b2: second 'byte' to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 3
        self.msg[2] = code & 0xFF
        self.msg[3] = b1 & 0xFF
        self.msg[4] = b2 & 0xFF
        self.msg[5] = self.end_index & 0xFF
        self.msg[6] = self.crc8(self.msg[2:5])
        self.msg_size = 7
        return self.msg_size

    def unpacketC2B(self) -> (int, int, int):
        """
        Unpackets the payload expecting a command code and two bytes
        :return: code and bytes
        """

        code = self.payload[0]
        b1 = self.payload[1]
        b2 = self.payload[2]
        return code, b1, b2

    def packetC3B(self, code: int, b1: int, b2: int, b3: int) -> int:
        """
        Packets bytes b1, b2 and b3 with command code + start and end indexes
        :param code:
        :param b1: first 'byte' to packet
        :param b2: second 'byte' to packet
        :param b3: third 'byte' to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 4
        self.msg[2] = code & 0xFF
        self.msg[3] = b1 & 0xFF
        self.msg[4] = b2 & 0xFF
        self.msg[5] = b3 & 0xFF
        self.msg[6] = self.end_index & 0xFF
        self.msg[7] = self.crc8(self.msg[2:6])
        self.msg_size = 8
        return self.msg_size

    def unpacketC3B(self) -> (int, int, int, int):
        """
        Unpackets the payload expecting a command code and three bytes
        :return: code and bytes
        """

        code = self.payload[0]
        b1 = self.payload[1]
        b2 = self.payload[2]
        b3 = self.payload[3]
        return code, b1, b2, b3

    def packetC1I(self, code: int, i: int) -> int:
        """
        Packets the int i with command code + start and end indexes
        :param code:
        :param i: the int to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 3
        self.msg[2] = code & 0xFF
        self.msg[3:5] = bytearray(struct.pack("h", i & 0xFFFF))
        self.msg[5] = self.end_index & 0xFF
        self.msg[6] = self.crc8(self.msg[2:5])
        self.msg_size = 7
        return self.msg_size

    def unpacketC1I(self) -> (int, int):
        """
        Unpackets the payload expecting a command code and one byte
        :return: code and int
        """

        code = self.payload[0]
        i = struct.unpack("h", self.payload[1:3])[0]
        return code, i

    def packetC2I(self, code: int, i1: int, i2: int) -> int:
        """
        Packets the ints with command code + start and end indexes
        :param code:
        :param i1: the 1st int to packet
        :param i2: the 2nd int to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 5
        self.msg[2] = code & 0xFF
        self.msg[3:5] = bytearray(struct.pack("h", i1 & 0xFFFF))
        self.msg[5:7] = bytearray(struct.pack("h", i2 & 0xFFFF))
        self.msg[7] = self.end_index & 0xFF
        self.msg[8] = self.crc8(self.msg[2:7])
        self.msg_size = 9
        return self.msg_size

    def unpacketC2I(self) -> (int, int, int):
        """
        Unpackets the payload expecting a command code and one byte
        :return: code and ints
        """

        code = self.payload[0]
        i1 = struct.unpack("h", self.payload[1:3])[0]
        i2 = struct.unpack("h", self.payload[3:5])[0]
        return code, i1, i2

    def packetC3I(self, code: int, i1: int, i2: int, i3: int) -> int:
        """
        Packets the ints with command code + start and end indexes
        :param code:
        :param i1: the 1st int to packet
        :param i2: the 2nd int to packet
        :param i3: the 3rd int to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 5
        self.msg[2] = code & 0xFF
        self.msg[3:5] = bytearray(struct.pack("h", i1 & 0xFFFF))
        self.msg[5:7] = bytearray(struct.pack("h", i2 & 0xFFFF))
        self.msg[7:9] = bytearray(struct.pack("h", i3 & 0xFFFF))
        self.msg[9] = self.end_index & 0xFF
        self.msg[10] = self.crc8(self.msg[2:9])
        self.msg_size = 11
        return self.msg_size

    def unpacketC3I(self) -> (int, int, int, int):
        """
        Unpackets the payload expecting a command code and one byte
        :return: code and ints
        """

        code = self.payload[0]
        i1 = struct.unpack("h", self.payload[1:3])[0]
        i2 = struct.unpack("h", self.payload[3:5])[0]
        i3 = struct.unpack("h", self.payload[5:7])[0]
        return code, i1, i2, i3

    def packetC7I(self, code: int, i1: int, i2: int, i3: int, i4: int, i5: int, i6: int, i7: int) -> int:
        """
        Packets the ints with command code + start and end indexes
        :param code:
        :param i1: the 1st int to packet
        :param i2: the 2nd int to packet
        :param i3: the 3rd int to packet
        :param i4: the 4th int to packet
        :param i5: the 5th int to packet
        :param i6: the 6th int to packet
        :param i7: the 7th int to packet
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 15
        self.msg[2] = code & 0xFF
        self.msg[3:5] = bytearray(struct.pack("h", i1 & 0xFFFF))
        self.msg[5:7] = bytearray(struct.pack("h", i2 & 0xFFFF))
        self.msg[7:9] = bytearray(struct.pack("h", i3 & 0xFFFF))
        self.msg[9:11] = bytearray(struct.pack("h", i4 & 0xFFFF))
        self.msg[11:13] = bytearray(struct.pack("h", i5 & 0xFFFF))
        self.msg[13:15] = bytearray(struct.pack("h", i6 & 0xFFFF))
        self.msg[15:17] = bytearray(struct.pack("h", i7 & 0xFFFF))
        self.msg[17] = self.end_index & 0xFF
        self.msg[18] = self.crc8(self.msg[2:17])
        self.msg_size = 19
        return self.msg_size

    def unpacketC7I(self) -> (int, int, int, int, int, int, int, int):
        """
        Unpackets the payload expecting a command code and one byte
        :return: code and ints
        """

        code = self.payload[0]
        i1 = struct.unpack("h", self.payload[1:3])[0]
        i2 = struct.unpack("h", self.payload[3:5])[0]
        i3 = struct.unpack("h", self.payload[5:7])[0]
        i4 = struct.unpack("h", self.payload[7:9])[0]
        i5 = struct.unpack("h", self.payload[9:11])[0]
        i6 = struct.unpack("h", self.payload[11:13])[0]
        i7 = struct.unpack("h", self.payload[13:15])[0]
        return code, i1, i2, i3, i4, i5, i6, i7

    def packetC1F(self, code: int, f: float) -> int:
        """
        Packets the float f with command code + start and end indexes
        :param code:
        :param f:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 5
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f))
        self.msg[7] = self.end_index & 0xFF
        self.msg[8] = self.crc8(self.msg[2:7])
        self.msg_size = 9
        return self.msg_size

    def unpacketC1F(self) -> (int, float):
        """
        Unpackets the payload expecting a command code and one float
        :return: code and float number
        """

        code = self.payload[0]
        f = struct.unpack("f", self.payload[1:5])[0]
        return code, f

    def packetC2F(self, code: int, f1: float, f2: float) -> int:
        """
        Packets the floats f1, f2 with command code + start and end indexes
        :param code:
        :param f1:
        :param f2:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 9
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f1))
        self.msg[7:11] = bytearray(struct.pack("f", f2))
        self.msg[11] = self.end_index & 0xFF
        self.msg[12] = self.crc8(self.msg[2:11])
        self.msg_size = 13
        return self.msg_size

    def unpacketC2F(self) -> (int, float, float):
        """
        Unpackets the payload expecting a command code and two floats
        :return: code, f1, f2
        """

        code = self.payload[0]
        f1 = struct.unpack("f", self.payload[1:5])[0]
        f2 = struct.unpack("f", self.payload[5:9])[0]
        return code, f1, f2

    def packetC3F(self, code: int, f1: float, f2: float, f3: float) -> int:
        """
        Packets the floats f1, f2, f3 with command code + start and end indexes
        :param code:
        :param f1:
        :param f2:
        :param f3:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 13
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f1))
        self.msg[7:11] = bytearray(struct.pack("f", f2))
        self.msg[11:15] = bytearray(struct.pack("f", f3))
        self.msg[15] = self.end_index & 0xFF
        self.msg[16] = self.crc8(self.msg[2:15])
        self.msg_size = 17
        return self.msg_size

    def unpacketC3F(self) -> (int, float, float, float):
        """
        Unpackets the payload expecting a command code and two floats
        :return: code, f1, f2, f3
        """

        code = self.payload[0]
        f1 = struct.unpack("f", self.payload[1:5])[0]
        f2 = struct.unpack("f", self.payload[5:9])[0]
        f3 = struct.unpack("f", self.payload[9:13])[0]
        return code, f1, f2, f3

    def packetC4F(self, code: int, f1: float, f2: float, f3: float, f4: float) -> int:
        """
        Packets the floats f1, f2, f3, f4 with command code + start and end indexes
        :param code:
        :param f1:
        :param f2:
        :param f3:
        :param f4:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 17
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f1))
        self.msg[7:11] = bytearray(struct.pack("f", f2))
        self.msg[11:15] = bytearray(struct.pack("f", f3))
        self.msg[15:19] = bytearray(struct.pack("f", f4))
        self.msg[19] = self.end_index & 0xFF
        self.msg[20] = self.crc8(self.msg[2:19])
        self.msg_size = 21
        return self.msg_size

    def unpacketC4F(self) -> (int, float, float, float, float):
        """
        Unpackets the payload expecting a command code and 4 floats
        :return: code, f1, f2, f3, f4
        """

        code = self.payload[0]
        f1 = struct.unpack("f", self.payload[1:5])[0]
        f2 = struct.unpack("f", self.payload[5:9])[0]
        f3 = struct.unpack("f", self.payload[9:13])[0]
        f4 = struct.unpack("f", self.payload[13:17])[0]
        return code, f1, f2, f3, f4

    def packetC6F(self, code: int, f1: float, f2: float, f3: float, f4: float, f5: float, f6: float) -> int:
        """
        Packets the floats f1, f2, f3, f4, f5, f6 with command code + start and end indexes
        :param code:
        :param f1:
        :param f2:
        :param f3:
        :param f4:
        :param f5:
        :param f6:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 25
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f1))
        self.msg[7:11] = bytearray(struct.pack("f", f2))
        self.msg[11:15] = bytearray(struct.pack("f", f3))
        self.msg[15:19] = bytearray(struct.pack("f", f4))
        self.msg[19:23] = bytearray(struct.pack("f", f5))
        self.msg[23:27] = bytearray(struct.pack("f", f6))
        self.msg[27] = self.end_index & 0xFF
        self.msg[28] = self.crc8(self.msg[2:27])
        self.msg_size = 29
        return self.msg_size

    def unpacketC6F(self) -> (int, float, float, float, float):
        """
        Unpackets the payload expecting a command code and 4 floats
        :return: code, f1, f2, f3, f4
        """

        code = self.payload[0]
        f1 = struct.unpack("f", self.payload[1:5])[0]
        f2 = struct.unpack("f", self.payload[5:9])[0]
        f3 = struct.unpack("f", self.payload[9:13])[0]
        f4 = struct.unpack("f", self.payload[13:17])[0]
        f5 = struct.unpack("f", self.payload[17:21])[0]
        f6 = struct.unpack("f", self.payload[21:25])[0]
        return code, f1, f2, f3, f4, f5, f6

    def packetC8F(self, code: int, f1: float, f2: float, f3: float, f4: float,
                  f5: float, f6: float, f7: float, f8: float) -> int:
        """
        Packets the floats f1, f2, f3, f4, f5, f6, f7, f8 with command code + start and end indexes
        :param code:
        :param f1:
        :param f2:
        :param f3:
        :param f4:
        :param f5:
        :param f6:
        :param f7:
        :param f8:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 33
        self.msg[2] = code & 0xFF
        self.msg[3:7] = bytearray(struct.pack("f", f1))
        self.msg[7:11] = bytearray(struct.pack("f", f2))
        self.msg[11:15] = bytearray(struct.pack("f", f3))
        self.msg[15:19] = bytearray(struct.pack("f", f4))
        self.msg[19:23] = bytearray(struct.pack("f", f5))
        self.msg[23:27] = bytearray(struct.pack("f", f6))
        self.msg[27:31] = bytearray(struct.pack("f", f7))
        self.msg[31:35] = bytearray(struct.pack("f", f8))
        self.msg[35] = self.end_index & 0xFF
        self.msg[36] = self.crc8(self.msg[2:35])
        self.msg_size = 37
        return self.msg_size

    def unpacketC8F(self) -> (int, float, float, float, float, float, float, float, float):
        """
        Unpackets the payload expecting a command code and 8 floats
        :return: code, f1, f2, f3, f4, f5, f6, f7, f8
        """

        code = self.payload[0]
        f1 = struct.unpack("f", self.payload[1:5])[0]
        f2 = struct.unpack("f", self.payload[5:9])[0]
        f3 = struct.unpack("f", self.payload[9:13])[0]
        f4 = struct.unpack("f", self.payload[13:17])[0]
        f5 = struct.unpack("f", self.payload[17:21])[0]
        f6 = struct.unpack("f", self.payload[21:25])[0]
        f7 = struct.unpack("f", self.payload[25:29])[0]
        f8 = struct.unpack("f", self.payload[29:33])[0]
        return code, f1, f2, f3, f4, f5, f6, f7, f8

    def packetC1B3F(self, code: int, b: int, f1: float, f2: float, f3: float) -> int:
        """
        Packets the byte b and the floats f1, f2, f3 with command code + start and end indexes
        :param code:
        :param b:
        :param f1:
        :param f2:
        :param f3:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 14
        self.msg[2] = code & 0xFF
        self.msg[3] = b & 0xFF
        self.msg[4:8] = bytearray(struct.pack("f", f1))
        self.msg[8:12] = bytearray(struct.pack("f", f2))
        self.msg[12:16] = bytearray(struct.pack("f", f3))
        self.msg[16] = self.end_index & 0xFF
        self.msg[17] = self.crc8(self.msg[2:16])
        self.msg_size = 18
        return self.msg_size

    def unpacketC1B3F(self) -> (int, int, float, float, float):
        """
        Unpackets the payload expecting a command code one byte and three floats
        :return: code, b, f1, f2, f3
        """

        code = self.payload[0]
        b = self.payload[1]
        f1 = struct.unpack("f", self.payload[2:6])[0]
        f2 = struct.unpack("f", self.payload[6:10])[0]
        f3 = struct.unpack("f", self.payload[10:14])[0]
        return code, b, f1, f2, f3

    def packetC2B1F(self, code: int, b1: int, b2: int, f: float) -> int:
        """
        Packets the bytes b1 and b2 and the float f with command code + start and end indexes
        :param code:
        :param b1:
        :param b2:
        :param f:
        :return: returns the size of the resulting msg array
        """

        self.msg[0] = self.start_index & 0xFF
        self.msg[1] = 7
        self.msg[2] = code & 0xFF
        self.msg[3] = b1 & 0xFF
        self.msg[4] = b2 & 0xFF
        self.msg[5:9] = bytearray(struct.pack("f", f))
        self.msg[9] = self.end_index & 0xFF
        self.msg[10] = self.crc8(self.msg[2:9])
        self.msg_size = 11
        return self.msg_size

    def unpacketC2B1F(self) -> (int, int, int, float):
        """
        Unpackets the payload expecting a command code and two floats
        :return: code, b1, b2, f
        """

        code = self.payload[0]
        b1 = self.payload[1]
        b2 = self.payload[2]
        f = struct.unpack("f", self.payload[3:7])[0]
        return code, b1, b2, f
