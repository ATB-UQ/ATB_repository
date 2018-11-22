from parsers.generic_parser import Run_Data

class GromosData(Run_Data):
    """A subclass of the Run_Data, to parse Gromos files only.
    It should be created once the file type is known."""

    def __init__(self, file):
        super().__init__(file)
        self._tags = [('num_timestep','NSTLIM', int), ('timestep', 'DT', float), ('initial_temperature', 'TEMPI', float),\
                      ('pressure', 'PRES0', float), ('bath_temperature', 'TEMP0', float), ('barostat', 'NTP', int)
                      ]

        self._parameters = {}
        self.find_parameters()

    def find_parameters(self):
        key_values = {**self.find_data(), **self.find_extras()}
        for tag in self._tags:
            key = tag[0]
            data_id = tag[1]
            data_type = tag[2]
            if key not in self._parameters:
                try:
                    self._parameters[key] = data_type(key_values[data_id])
                except (TypeError, KeyError) as error:
                    pass

    def find_data(self):
        """Finds all keys and values which can be easily extracted."""
        key_values = {}
        for i in range(len(self._file_list)):
            line = self._file_list[i].split()
            if line[0].isdigit():
                values = line
                keys = self._file_list[i - 1].split()
                if keys[0] is '#':
                    keys.pop(0)
                if keys[0].isalpha():
                    for x in range(len(values)):
                        try:
                            key_values[keys[x]] = values[x]
                        except IndexError:
                            continue
        return key_values

    def find_extras(self):
        """Calls all the extra functions. Returns all the extra values in a dictionary"""
        return {**self.find_pressure_temperature()}

    def find_pressure_temperature(self):
        """Finds the pressure and bath temperature data.
        Return:
            pressure_values: dict(string = string)"""
        extra_values = {}
        for i in range(len(self._file_list)):
            line = self._file_list[i].split()
            if line[0] == '#':
                line.pop(0)
            try:
                key = line[0].split('(')[0]
                if key == 'PRES0':
                    value = self._file_list[i+1].split()[0]
                    extra_values[key] = value
                elif key == 'TEMP0':
                    value = self._file_list[i+2].split()[0]
                    extra_values[key] = value
            except IndexError:
                continue
        return extra_values