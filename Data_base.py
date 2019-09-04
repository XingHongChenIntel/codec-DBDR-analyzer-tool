import pickle
import os
from Data_struct import Line, LineContain, CaseDate


class Database:
    def __init__(self, datapath):
        self.datapath = datapath
        self.data = self.deserialize_data()
        self.temp_case = None

    def is_data_exist(self):
        return os.path.exists(self.datapath)

    def deserialize_data(self):
        if self.is_data_exist():
            f = open(self.datapath, 'rb')
            data = pickle.load(f)
            f.close()
            return data
        else:
            data = CaseDate()
            return data

    def find_data(self, yuv_info, encode_name, tag):
        if len(self.data.case) == 0:
            self.build_case(yuv_info)
            self.build_encode(encode_name)
            return False, None
        if self.is_have_yuv(yuv_info):
            if self.is_have_encode(encode_name):
                if tag == 'read':
                    return True, self.temp_case.group[encode_name]
                else:
                    self.temp_case.group[encode_name] = []
                    self.temp_case.group_bdrate[encode_name] = []
                    return False, None
        else:
            self.build_encode(encode_name)
            return False, None
        return False, None

    def is_have_yuv(self, yuv_info):
        yuv_contain = [pic.yuv_info for pic in self.data.case]
        if yuv_info in yuv_contain:
            self.temp_case = self.data.case[yuv_contain.index(yuv_info)]
            return True
        else:
            self.build_case(yuv_info)
            return False

    def is_have_encode(self, encode_name):
        if encode_name in self.temp_case.group.keys():
            return True
        else:
            self.build_encode(encode_name)
            return False

    def build_encode(self, encode_name):
        self.temp_case.group[encode_name] = []
        self.temp_case.group_bdrate[encode_name] = []

    def build_case(self, yuv_info):
        line_pool = LineContain()
        line_pool.set_data_type(yuv_info)
        self.data.case.append(line_pool)
        self.temp_case = self.data.case[-1]

    def add_data(self, line, encode_name):
        self.temp_case.group[encode_name].append(line)

    def serialize_date(self):
        f = open(self.datapath, 'wb')
        pickle.dump(self.data, f)
        f.close()
