import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class AtbsearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config_):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'atbsearch')