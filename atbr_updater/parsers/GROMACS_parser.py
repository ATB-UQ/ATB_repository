from parsers.generic_parser import *

class GromacsData(Run_Data):
    """A subclass of the Run_Data, to parse GROMACS files only.
    It should be created once the file type is known."""

    def __init__(self, file):
        super().__init__(file)

        self._tags = [('num_timestep','nsteps', int), ('timestep', 'dt', float), ('temperature', 'ref_t', array),\
                      ('cutoff', 'rvdw', float), ('shake_tolerance', 'tol', float), ('barostat', 'Pcoupltype', str), \
                      ('pressure', 'tau-p', float), ('thermostat', 'tcoupl', str)]

        self._parameters = {'program': 'GROMACS'}
        self.find_parameters()
        self.calc_runtime()

    def find_parameters(self):
        for line in self._file_list:
            for tag in self._tags:
                key = tag[0]
                data_id = tag[1]
                data_type = tag[2]
                if key not in self._parameters:
                    try:
                        data = self.find_data(line, data_id)
                        if data is not None: # only adds the key/data pair if data is not none
                            self._parameters[key] = data_type(data)
                    except (TypeError, AttributeError) as error:
                        continue

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
            line_tag = line_tag.strip()
        except ValueError:
            pass
        if line_tag == tag:
            data = line_data.strip()
        return data

def array(string):
    """Converts string to a list, split on whitespace
    :param:
    string(str): The string to split
    :return
    string.split()(list): The string split into a list on the white space."""
    return string.split()