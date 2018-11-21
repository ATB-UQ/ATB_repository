class Run_Data(object):
    """Parent class for runs. """
    def __init__(self, file):
        self._file = file

        self._file_list = []
        for line in file:
            line = line.rstrip()
            line = line.strip()
            self._file_list.append(line)

        if self._file_list[2] == '&cntrl':
            self._type = 'amber'

    def get_type(self):
        return self._type

    def find_parameters(self):
        """Must be implemented by the subclasses"""
        pass


class Amber_Data(Run_Data):
    """A subclass of the Run_Data, to parse Amber files only.
    It should be created once the file type is known."""

    def __init__(self, file):
        super().__init__(file)

        self._tags = [('num_timestep','nstlim', int), ('timestep', 'dt', float), ('temperature', 'temp0', float),\
                      ('cutoff', 'cut', float), ('shake_tolerance', 'tol', float), ('barostat', 'barostat', int), \
                      ('pressure', 'pres0', float), ('thermostat', 'ntt', int)]

        self._barostat = {1:'Berendsen', 2:'Monte Carlo'}
        self._thermostat = {1:'Berendsen'}

        self._parameters = {}

        self.find_parameters()

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

    def get_parameters(self):
        return self._parameters

    def get_file(self):
        return self._file_list

    def add_tag(self, name, tag_id, type):
        """Adds a new tag to self._tags.
        :param:
        name(str): The name of the tag
        tag_id(str): The id of the tag in the file
        type(class): The type of the data. eg. str, int, float."""

        tag = (name, tag_id, type)
        self._tags.append(tag)