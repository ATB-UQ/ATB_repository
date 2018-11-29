from parsers.generic_parser import *

class AmberData(Run_Data):
    """A subclass of the Run_Data, to parse Amber files only.
    It should be created once the file type is known."""

    def __init__(self, control_file, log_file, energy_file):
        super().__init__(control_file, log_file, energy_file)
                        # key, id in file, data type, number to multiply by to standardise
        self._tags = [('num_timestep','nstlim', int), ('timestep', 'dt', float), ('temperature', 'temp0', float),\
                      ('cutoff', 'cut', float), ('shake_tolerance', 'tol', float), ('barostat', 'barostat', int),\
                      ('pressure', 'pres0', float), ('thermostat', 'ntt', int)]

        self._barostat = {1:'Berendsen', 2:'Monte Carlo'}
        self._thermostat = {1:'Berendsen'}

        self._parameters = {'program': 'AMBER'}
        self.find_parameters()
        self.calc_runtime()
        self._parameters['num_atoms'] = self.find_atoms()

        energy_list = self.get_energy_data(self._energy_file)
        energy_matrices = self.nest_values(energy_list)
        self._initial_energy = self.matrix2dict(energy_matrices)
        self.find_box()

    def find_box(self):
        boxX, boxY, boxZ, = self._initial_energy['BoxX'], self._initial_energy['BoxY'], self._initial_energy['BoxZ']

        if boxX == boxY == boxZ:
            self._parameters['box_side'] = float(boxX)
        else:
            self._parameters['box_side'] = -1

    def find_parameters(self):
        for line in self._file_list:
            for tag in self._tags:
                key = tag[0]
                data_id = tag[1]
                data_type = tag[2]

                if key not in self._parameters:
                    try:
                        data = data_type(self.find_data(line, data_id))
                        self._parameters[key] = data
                        if key == 'barostat':
                            self._parameters[key] = self._barostat.get(data)
                        if key == 'thermostat':
                            self._parameters[key] = self._thermostat.get(data)
                    except TypeError:
                        pass

    def find_data(self, line, tag):
        """Determines if the line contains info on the 'tag', and if so, returns the corresponding data.
        :param
        line(str): The line to be processed. Must have all trailing characters stripped.
        :return
        data(str/None) The tag's data, or None, if tag not found."""

        line_data = None
        line_tag = None
        data = None

        try:
            line_tag, line_data = line.split('=')
        except ValueError:
            pass
        if line_tag == tag:
            data = line_data.strip(',')
        return data


    def find_atoms(self):
        reading_atoms = False
        with open(self._log_file, 'r') as file:
            for line in file:
                line = line.rstrip()
                line = line.split()
                try:
                    if line[0] == 'NATOM':
                        num_atoms = line[2]
                except IndexError:
                    continue
        return int(num_atoms)

    def get_energy_data(self, energy_file):
        """Sets self._energy_list to a list of the lines from file"""
        i = 0
        file_list = []
        with open(energy_file, 'r') as file:
            for line in file:
                if i<21:
                    i += 1
                    line = line.split()
                    line.pop(0)  # remove L# from the line
                    file_list.append(line)
        return file_list

    def nest_values(self, energy_list):
        """Turns self._energy_list into a list of nested lists.
      [ [x1,y1]  [x2,y2] ]
        [w1.z1], [w2,z2] """
        matrix = []
        i = 0
        nest = []
        for line in energy_list:
            if i == 10:
                matrix.append(nest)
                nest = []
                i = 0
            nest.append(line)
            i += 1
        return matrix

    def matrix2dict(self, matrices):
        """Turns matrices into a dictionary of lists, with the first matrix as the keys"""
        columns = 4
        rows = 10
        data_dict = {}
        for x in range(rows):
            for y in range(columns):
                for i in range(len(matrices)):
                    if i == 0:
                        data_dict[matrices[i][x][y]] = []
                    else:
                        data_dict[matrices[0][x][y]] = matrices[i][x][y]
        return data_dict
