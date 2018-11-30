from parsers.generic_parser import *

class GromosData(RunData):
    """A subclass of the Run_Data, to parse Gromos files only.
    It should be created once the file type is known."""

    def __init__(self, control_file, log_file, energy_file):
        super().__init__(control_file, log_file, energy_file)
                        # key, id in file, data type, number to multiply by to standardise
        self._tags = [('num_timestep','NSTLIM', int), ('timestep', 'DT', float), ('initial_temperature', 'TEMPI', float),\
                      ('pressure', 'PRES0', float), ('bath_temperature', 'TEMP0', float), ('barostat', 'NTP', int)
                      ]

        self._barostat = {0: 'None', 1: 'Pressure Constraining', 2: 'Berendsen', 3: 'Nose-Hover'}
        self._thermostat = {1: 'Berendsen'}

        self._parameters = {'program': 'GROMOS'}
        self._parameters['num_atoms'] = self.find_atoms()
        self._parameters['box_side'] = -1
        self.find_parameters()
        self.calc_runtime()

    def find_parameters(self):
        key_values = {**self.find_data(), **self.find_extras()}
        for tag in self._tags:
            key = tag[0]
            data_id = tag[1]
            data_type = tag[2]
            if key not in self._parameters:
                try:
                    self._parameters[key] = data_type(key_values[data_id])
                    if key == 'barostat':
                        self._parameters[key] = self._barostat.get(data)
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
                    decimals = len(value) - 1 #Minus 1 to remove the decimal
                    value = float(value) * 16.6057 #Convert pressure to bars
                    value = round(value, decimals)
                    extra_values[key] = value
                elif key == 'TEMP0':
                    value = self._file_list[i+2].split()[0]
                    extra_values[key] = value
            except IndexError:
                continue
        return extra_values

    def find_atoms(self):
        with open(self._log_file, 'r') as file:
            for line in file:
                line = line.rstrip()
                if 'number of atoms' in line:
                    line = line.split()
                    num_atoms = line[-1]
        print(num_atoms)
        return int(num_atoms)