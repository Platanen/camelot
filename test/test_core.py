import unittest
from camelot.test import ModelThreadTestCase

class CoreCase(ModelThreadTestCase):
    """test functions from camelot.core
    """
            
    def test_session_refresh(self):
        from camelot.model.authentication import Person
        session = Person.query.session
        #
        # create objects in various states
        #
        p1 = Person(first_name = 'p1', last_name = 'persistent' )
        p2 = Person(first_name = 'p2', last_name = 'dirty' )
        p3 = Person(first_name = 'p3', last_name = 'deleted' )
        p4 = Person(first_name = 'p4', last_name = 'to be deleted' )
        p5 = Person(first_name = 'p5', last_name = 'detached' )
        session.flush()
        p3.delete()
        session.flush()
        p4.delete()
        p2.last_name = 'clean'
        
        from camelot.core.orm import refresh_session
        refresh_session( session )
        
        self.assertEqual( p2.last_name, 'dirty' )
        print p3.name
        print p4.name
        
class ConfCase(unittest.TestCase):
    """Test the global configuration"""
    
    def test_import_settings(self):
        from camelot.core.conf import settings
        self.assertRaises( AttributeError, lambda:settings.FOO )
        self.assertEqual( settings.CAMELOT_MEDIA_ROOT, 'media' )