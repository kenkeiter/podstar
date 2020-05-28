import datetime
from unittest import mock

import pytest

from podstar import episode


class TestEpisode:

    @pytest.fixture(scope='class', params=[
        (30.0, '00:00:30'),
        (1800.0, '00:30:00'),
        (3600.0, '01:00:00'),
        (30.0, '30'),
        (1800.0, '30:00'),])
    def itunes_time_format(self, request):
        """
        Generate an assortment of weirdly-formatted iTunes durations.
        """
        return request.param

    def test_from_xml_item(self, xml_template):
        """
        Episodes should be creatable from an XML <item> element.
        """
        # lol, RSS pubDates _don't_ encode nanoseconds I guess
        # get a datetime rounded to the latest second
        now = datetime.datetime.now()
        now = datetime.datetime(
            now.year, now.month, now.day, now.hour, now.minute, now.second, 
            microsecond=0, tzinfo=now.tzinfo)

        item_attrs = {
            'title': "An Item",
            'description': "Item Description",
            'pubdate': now,
            'itunes': True,
            'enclosure_url': 'http://example.com/example.mp3',
        }

        tree = xml_template('single_item.xml', **item_attrs)
        ep = episode.Episode.from_xml_item(None, tree.find('item'))
        
        assert ep.title == item_attrs['title'], \
            "title should be parsed from xml item that includes it"
        assert ep.description == item_attrs['description'], \
            "description should be parsed from xml item that includes it"
        assert ep.published_at == item_attrs['pubdate'], \
            "datetime should be properly parsed"
        assert ep.get('enclosure').attrs['url'] == item_attrs['enclosure_url'], \
            "enclosure url should be properly parsed"

        assert ep.duration == 2189.0, \
            "duration should be parsed from iTunes annotation when possible"

        assert len(ep.errors) == 0, \
            "no errors should have occurred during parsing"

    def test_soft_duration(self, mocker, xml_template, itunes_time_format):
        """
        When an episode includes iTunes duration annotations, they should be 
        used to provide the duration of the episode.
        """
        seconds, time_repr = itunes_time_format
        tree = xml_template(
            'single_item.xml',
            title="Test Item",
            itunes=True,
            itunes_duration=time_repr)
        audio = mocker.patch('podstar.episode.Episode.audio', 
            new_callable=mock.PropertyMock, return_value=None)
        ep = episode.Episode.from_xml_item(None, tree.find('item'))
        assert ep.soft_duration == seconds, \
            "episode duration should be determinable using itunes attrs"
        assert ep.duration == seconds, \
            "episode duration should be determined using itunes attrs"
        assert not audio.called, \
            "episode AudioEnclosure should not be used to determine duration"

    def test_duration(self):
        """
        When an episode's duration cannot be determined using iTunes 
        annotations, the enclosed audio file should be inspected to determine 
        the duration.
        """
        ep = episode.Episode(None, "Test Episode")
        ep._audio = mock.MagicMock()
        type(ep._audio).duration = mock.PropertyMock(return_value=30.0)

        assert ep.duration == 30.0, \
            "when enclosed audio is available and no itunes annotations are " \
            "available, duration should be determined by inspecting audio file"
