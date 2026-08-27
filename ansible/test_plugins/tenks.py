class TestModule(object):
    '''Tenks tests.'''

    def tests(self):
        return {
            # Libvirt tests.
            'requires_libvirt_configuration': requires_libvirt_configuration,
        }


def requires_libvirt_configuration(node):
    """Select nodes that require configuration in Libvirt."""
    return node.get('state') == 'absent' or node.get('instantiating') is True
