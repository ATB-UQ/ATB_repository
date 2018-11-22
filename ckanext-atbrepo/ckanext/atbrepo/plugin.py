import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

def create_programs():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'programs'}
        toolkit.get_action('vocabulary_show')(context, data)
        logging.info("Programs vocabulary already exists, skipping.")
    except toolkit.ObjectNotFound:
        logging.info("Creating vocab 'programs'")
        data = {'name': 'programs'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'GROMACS', u'GROMOS', u'AMBER', u'LAMMPS', u'CHARMM'):
            logging.info(
                    "Adding tag {0} to vocab 'programs'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def create_barostats():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'barostats'}
        toolkit.get_action('vocabulary_show')(context, data) # Attempts to retrieve the barostat vocabulary to
                                                             # see if it already exists.
        logging.info("barostats vocabulary already exists, skipping.")
    except toolkit.ObjectNotFound:
        logging.info("Creating vocab 'barostats'")
        data = {'name': 'barostats'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Berendsen', u'Monte Carlo', u'None'): #Add barostat types here
            logging.info(
                    "Adding tag {0} to vocab 'barostats'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def create_thermostats():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'thermostats'}
        toolkit.get_action('vocabulary_show')(context, data) # Attempts to retrieve the thermostat vocabulary to
                                                             # see if it already exists.
        logging.info("thermostats vocabulary already exists, skipping.")
    except toolkit.ObjectNotFound:
        logging.info("Creating vocab 'thermostats'")
        data = {'name': 'thermostats'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Berendsen', u'Monte Carlo'): #Add thermostat types here
            logging.info(
                    "Adding tag {0} to vocab 'thermostats'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def thermostats():
    create_thermostats()
    try:
        tag_list = toolkit.get_action('tag_list')
        thermostats = tag_list(data_dict={'vocabulary_id': 'thermostats'})
        return thermostats
    except toolkit.ObjectNotFound:
        return None

def barostats():
    create_barostats()
    try:
        tag_list = toolkit.get_action('tag_list')
        barostats = tag_list(data_dict={'vocabulary_id': 'barostats'})
        return barostats
    except toolkit.ObjectNotFound:
        return None

def programs():
    create_programs()
    try:
        tag_list = toolkit.get_action('tag_list')
        programs = tag_list(data_dict={'vocabulary_id': 'programs'})
        return programs
    except toolkit.ObjectNotFound:
        return None

def get_resource_types(resources):
    """
    jinja2 helper fuction to get the list of unique resource types
    """
    return set( resource["resource_type"] for resource in resources )


class AtbrepoPlugin(plugins.SingletonPlugin,  toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)
    #plugins.implements(plugins.ITemplateHelpers)


    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'atbrepo')

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):

        # Add temperature field
        schema.update({
        'temperature': [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')],
        'pressure': [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')],
        'initial_temperature': [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')],
        'simulation_time': [
            toolkit.get_validator('ignore_missing'),
            toolkit.get_converter('convert_to_extras')],
        })

        # Add program tags
        schema.update({
            'program': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('programs')
            ],
            # Add barostat tags
            'barostat': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('barostats')
            ],
            # Add thermostat tags
            'thermostat': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('thermostats')
            ],
        })

        # Add run metadata field to the resodataurce schema
        schema['resources'].update({
            'run' : [ toolkit.get_validator('is_positive_integer') ]
        })

        return schema

    def create_package_schema(self):
        schema = super(AtbrepoPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(AtbrepoPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(AtbrepoPlugin, self).show_package_schema()
        schema.update({
            'temperature': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_from_extras')],
            'pressure': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_from_extras')],
            'initial_temperature': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_from_extras')],
            'simulation_time': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_from_extras')],
        })

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        # add custom program tag to the schema
        schema.update({
            'program': [
                toolkit.get_converter('convert_from_tags')('programs'),
                toolkit.get_validator('ignore_missing')],
            'barostat': [
                toolkit.get_converter('convert_from_tags')('barostats'),
                toolkit.get_validator('ignore_missing')],
            'thermostat': [
                toolkit.get_converter('convert_from_tags')('thermostats'),
                toolkit.get_validator('ignore_missing')],
        })

        # Validates run metadata field for resources before showing to user
        schema['resources'].update({
            'run' : [ toolkit.get_validator('is_positive_integer') ]
        })

        return schema

    def get_helpers(self):
        '''Register the template helper functions.
        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
	    'atbrepo_get_resource_types': get_resource_types,
            'programs': programs,
            'barostats': barostats,
            'thermostats': thermostats,
	}


