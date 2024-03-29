class RunData(object):
    """Parent class for runs. """
    def __init__(self, control_file, log_file=None, energy_file=None):
        self._control_file = control_file
        self._log_file = log_file
        self._energy_file = energy_file

        self._parameters = {}
        self._tags = []

        self._file_list = []
        with open(control_file) as file:
            for line in file:
                line = line.rstrip()
                line = line.strip()
                self._file_list.append(line)

        if self._file_list[2] == '&cntrl':
            self._type = 'AMBER'
        elif self._file_list[0] == 'TITLE':
            self._type = 'GROMOS'
        if ';' in self._file_list[1]:
            self._type = 'GROMACS'


    def get_type(self):
        return self._type

    def find_parameters(self):
        """Must be implemented by the subclasses"""
        pass

    def calc_runtime(self):
        timestep = self._parameters['timestep']
        self._parameters['runtime'] = (timestep * self._parameters['num_timestep'])/1000

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

    def standard_units(self):
        """Converts the units in self._parameters to standardised units.
        Pressure --> Bar
        Temperature --> Kelvin
        """
        for tag in self._tags:
            key = tag[0]
            value = self._parameters[key]
            try:
                standard = tag[3]
                value = value * standard
                self._parameters[key] = value
            except IndexError:
                continue
