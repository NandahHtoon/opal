"""
Unittests for opal.core.trade
"""
import copy
import datetime

from opal.core.test import OpalTestCase
from opal.models import Patient
from opal.tests.models import Birthday

from opal.core import trade


class AbstractSpikeMilliganTestCase(OpalTestCase):

    _data = {
        'episodes': {
            '239789': {
                'start': '22/02/2018',
                'end'  : '28/02/2018',
                'colour': [
                    {'name': 'Blue'}, {'name': 'Red'}, {'name': 'Green'}
                ]
            }
        },
        'demographics': [
            {
                'first_name'   : 'Spike',
                'surname'      : 'Milligan',
                'date_of_birth': '16/04/1918'
            }
        ],
        'favourite_number': [
            {'number': 23}, {'number': 7}, {'number': 13}
        ],
        'famous_last_words': [
            {'words': "I told you I was ill."}
        ]
    }

    def data(self):
        return copy.copy(self._data)



class ExportMatcherTestCase(OpalTestCase):

    def test_get_demographic_dict(self):
        matcher = trade.OpalExportMatcher({'hello': 'world'})
        self.assertEqual(
            {'hello': 'world'}, matcher.get_demographic_dict()
        )


class ImportPatientSubrecordDataTestCase(OpalTestCase):

    def test_import_subrecord_data(self):
        patient, episode = self.new_patient_and_episode_please()
        data = [{'number': 23}, {'number': 7}, {'number': 13}]

        trade.import_patient_subrecord_data(
            'favourite_number',
            data,
            patient
        )
        numbers = [f.number for f in patient.favouritenumber_set.all()]
        for i in [23, 7, 13]:
            self.assertIn(i, numbers)


class CreateEpisodeForPatientTestCase(OpalTestCase):

    def test_create_episode(self):
        patient = Patient.objects.create()

        data = {
            'start': '22/02/2018',
            'end'  : '28/02/2018',
            'colour': [
                {'name': 'Blue'}, {'name': 'Red'}, {'name': 'Green'}
            ]
        }

        trade.create_episode_for_patient(patient, data)

        episode = patient.episode_set.get()

        self.assertEqual(datetime.date(2018, 02, 22), episode.start)
        self.assertEqual(datetime.date(2018, 02, 28), episode.end)

        colours = [c.name for c in episode.colour_set.all()]
        for c in ['Blue', 'Red', 'Green']:
            self.assertIn(c, colours)


class ImportPatientTestCase(AbstractSpikeMilliganTestCase):


    def test_import_patient(self):

        trade.import_patient(self.data())

        patient = Patient.objects.get(
            demographics__first_name='Spike',
            demographics__surname='Milligan',
            demographics__date_of_birth='1918-04-16'
        )
        episode = patient.episode_set.get()

        self.assertEqual(datetime.date(2018, 02, 22), episode.start)
        self.assertEqual(datetime.date(2018, 02, 28), episode.end)

        numbers = [f.number for f in patient.favouritenumber_set.all()]
        for i in [23, 7, 13]:
            self.assertIn(i, numbers)

        colours = [c.name for c in episode.colour_set.all()]
        for c in ['Blue', 'Red', 'Green']:
            self.assertIn(c, colours)

        words = patient.famouslastwords_set.get()
        self.assertEqual('I told you I was ill.', words.words)

    def test_import_patient_matched(self):
        p, e = self.new_patient_and_episode_please()
        p.demographics_set.update(
            first_name='Spike',
            surname='Milligan',
            date_of_birth='1918-04-16'
        )
        trade.import_patient(self.data())


        patient = Patient.objects.get(
            demographics__first_name='Spike',
            demographics__surname='Milligan',
            demographics__date_of_birth='1918-04-16'
        )
        self.assertEqual(p.id, patient.id)
        self.assertEqual(2, patient.episode_set.count())

        episode = patient.episode_set.last()

        self.assertEqual(datetime.date(2018, 02, 22), episode.start)
        self.assertEqual(datetime.date(2018, 02, 28), episode.end)

        numbers = [f.number for f in patient.favouritenumber_set.all()]
        for i in [23, 7, 13]:
            self.assertIn(i, numbers)

        colours = [c.name for c in episode.colour_set.all()]
        for c in ['Blue', 'Red', 'Green']:
            self.assertIn(c, colours)

        words = patient.famouslastwords_set.get()
        self.assertEqual('I told you I was ill.', words.words)


class PatientIDToJSONTestCase(AbstractSpikeMilliganTestCase):

    def test_patient_to_json(self):
        p, e = self.new_patient_and_episode_please()
        p.demographics_set.update(
            first_name='Spike',
            surname='Milligan',
            date_of_birth='1918-04-16'
        )
        p.favouritenumber_set.create(number=23)
        p.favouritenumber_set.create(number=7)
        p.favouritenumber_set.create(number=13)
        p.famouslastwords_set.update(words='I told you I was ill.')
        e.start = datetime.date(2018, 02, 22)
        e.end   = datetime.date(2018, 02, 28)
        e.id = 239789
        e.save()
        e.colour_set.create(name='Blue')
        e.colour_set.create(name='Red')
        e.colour_set.create(name='Green')
        p.episode_set.get(id=1).delete()

        data, patient = trade.patient_id_to_json(p.id)

        self.assertEqual('Spike', data['demographics'][0]['first_name'])
        self.assertEqual('Milligan', data['demographics'][0]['surname'])
        self.assertEqual(datetime.date(2018, 02, 22), data['episodes'][239789]['start'])
        self.assertEqual(datetime.date(2018, 02, 28), data['episodes'][239789]['end'])
        self.assertEqual(
            [
                {'name': 'Blue'}, {'name': 'Red'}, {'name': 'Green'}
            ],
            data['episodes'][239789]['colour']
        )
        self.assertEqual(
             [
                 {'number': 23}, {'number': 7}, {'number': 13}
             ],
            data['favourite_number']
        )
        self.assertEqual(
            [{'words': 'I told you I was ill.'}],
            data['famous_last_words']
        )
        data['favourite_colour']


    def test_patient_to_json_excludes(self):
        p, e = self.new_patient_and_episode_please()
        p.demographics_set.update(
            first_name='Spike',
            surname='Milligan',
            date_of_birth='1918-04-16'
        )
        p.favouritenumber_set.create(number=23)
        p.favouritenumber_set.create(number=7)
        p.favouritenumber_set.create(number=13)

        data, patient = trade.patient_id_to_json(p.id, excludes=['favourite_number'])

        self.assertNotIn('favourite_number', data)