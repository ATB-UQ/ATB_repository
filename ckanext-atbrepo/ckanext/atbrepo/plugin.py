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
    plugins.implements(plugins.ITemplateHelpers)


    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'atbrepo')

    def get_helpers(self):
        return {'programs': programs}

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):

        # Add program tags
        schema.update({
            'program': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('programs')
            ]
        })

        # Add run metadata field to the resource schema
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

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        # add custom program tag to the schema
        schema.update({
            'program': [
                toolkit.get_converter('convert_from_tags')('programs'),
                toolkit.get_validator('ignore_missing')]
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
        return {'atbrepo_get_resource_types': get_resource_types}


