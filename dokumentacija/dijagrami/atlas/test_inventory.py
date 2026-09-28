"""Regression checks for cardinalities and ownership; no Django initialization."""
from pathlib import Path
import tempfile
import unittest

from models import inspect_sources

class ModelInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for module in ['core','hr','demo']:(self.root/module).mkdir()
        (self.root/'core/models.py').write_text('''
class CustomUser(models.Model):
    name = models.CharField(max_length=40)
    class Meta: app_label = 'fleet'
''')
        (self.root/'hr/models.py').write_text('''
class Employee(models.Model):
    code = models.CharField(max_length=20)
    class Meta: app_label = 'fleet'
''')
        (self.root/'demo/models.py').write_text('''
class Tracked(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    class Meta: abstract = True
class Request(Tracked):
    employee = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT)
    code = models.CharField(max_length=20)
class Decision(Tracked):
    request = models.ForeignKey(Request, on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['request'], name='one_request')]
class Version(models.Model):
    employee = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['employee'], condition=models.Q(active=True), name='active_only')]
class Legacy(models.Model):
    code = models.CharField(max_length=20)
    class Meta:
        managed = False
        db_table = 'existing_view'
''')
        self.models,self.edges=inspect_sources(self.root,['core','hr','demo'])
    def tearDown(self):self.temp.cleanup()
    def edge(self,model,field):return next(e for e in self.edges if e['source']==model and e['field']==field)
    def test_unconditional_unique_fk_is_optional_reverse_single(self):
        edge=self.edge('demo.Decision','request')
        self.assertEqual((edge['left'],edge['right']),('0..1','1'))
    def test_conditional_unique_keeps_history_many_to_one(self):
        edge=self.edge('demo.Version','employee')
        self.assertEqual((edge['left'],edge['right']),('0..*','1'))
    def test_abstract_inheritance_keeps_declaring_source_and_resolves_user(self):
        self.assertTrue(self.models['demo.Tracked']['abstract'])
        self.assertIsNone(self.models['demo.Tracked']['table'])
        self.assertFalse(self.models['demo.Request']['abstract'])
        edge=self.edge('demo.Request','actor')
        self.assertEqual(edge['target'],'core.CustomUser');self.assertEqual(edge['right'],'0..1')
        self.assertTrue(edge['inherited'])
    def test_app_label_is_not_source_module(self):
        self.assertEqual(self.edge('demo.Request','employee')['target'],'hr.Employee')
        self.assertEqual(self.models['hr.Employee']['table'],'fleet_employee')
    def test_shared_text_codes_are_not_fk_and_legacy_is_unmanaged(self):
        self.assertFalse(any(e['field']=='code' for e in self.edges))
        self.assertFalse(self.models['demo.Legacy']['managed'])
        self.assertEqual(self.models['demo.Legacy']['table'],'existing_view')

if __name__=='__main__':unittest.main()
