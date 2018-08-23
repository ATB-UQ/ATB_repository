import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class AtbrepoPlugin(plugins.SingletonPlugin):
    # plugins.implements(p.IDatasetForm) #this  might be needed later?
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
       #toolkit.add_resource('fanstatic', 'atbrepo')

    def _modify_package_schema(self, schema):
        # Add run metadata field to the resource schema
        schema['resources'].update({
            'run' : [ tk.get_validator('is_positive_integer') ]
        })
        return schema

    def show_package_schema(self):
        # Validates run metadata field for resources before showing to user
        schema['resources'].update({
            'run' : [ tk.get_validator('is_positive_integer') ]
        })
        return schema

