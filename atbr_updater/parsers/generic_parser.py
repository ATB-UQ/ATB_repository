class Run_Data(object):
    """Parent class for runs. """
    def __init__(self, control_file):
        self._file = control_file

        self._parameters = {}
        self._tags = []

        self._file_list = []
        with open(control_file) as file:
            for line in file:
                line = line.rstrip()
                line= line.strip()
                self._file_list.append(line)

        if self._file_list[2] == '&cntrl':
            self._type = 'amber'
        elif self._file_list[0] == 'TITLE':
            self._type = 'gromos'


    def get_type(self):
        return self._type

    def find_parameters(self):
        """Must be implemented by the subclasses"""
        pass

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