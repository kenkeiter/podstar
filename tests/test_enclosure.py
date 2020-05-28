import io
import types
import tempfile
import collections
from unittest import mock

import pytest
import requests
import requests_mock
import mutagen
import mutagen.mp3
import mutagen.mp4

from podstar import enclosure

FileExtPermutation = collections.namedtuple('FileExtPermutation', 
    ['url', 'filename', 'ext', 'metadata_cls'])

class TestAudioEnclosure:

    @pytest.fixture(
        params=[
            FileExtPermutation(
                url='http://example.com/path/to/my.mp3',
                filename='my.mp3', ext='.mp3',
                metadata_cls=mutagen.mp3.MP3),
            FileExtPermutation(
                url='http://example.com/download/mp4/?id=123',
                filename='', ext='.m4a',
                metadata_cls=mutagen.mp4.MP4),
            ])
    def audio_file(cls, request):
        filename, ext, url, metadata_cls = request.param
        yield (filename, ext, url, metadata_cls)

    def test_filename(self, audio_file):
        """
        AudioEnclosure should be able to extract the original filename from the 
        URL, whenever possible.
        """
        metadata = mutagen.mp3.MP3()
        ae = enclosure.AudioEnclosure(None, 'http://example.com/path/to/my.mp3')
        ae._metadata = metadata

        assert (ae.filename == 'my.mp3'), \
            "filenames should be extracted from the URL, when possible"

        ae = enclosure.AudioEnclosure(None, 'http://example.com/download/mp4/?id=123')
        assert (ae.filename == ''), \
            "filename should be empty when it cannot be extracted from the URL"

    def test_filename_ext(self, mocker):
        """
        AudioEnclosure should be able to determine an appropriate filename 
        extension regardless of whether one was included in the URL.
        """
        ae = enclosure.AudioEnclosure(None, 'http://example.com/path/to/my.mp3')

        # mock os.path.splitext so we can ensure it's used to determine filename
        splitext_mock = mocker.patch('os.path.splitext', return_value=('my', '.mp3'))

        assert (ae.filename_ext == '.mp3'), \
            "filename_ext should be determined properly from the URL, " \
            "when provided"
        splitext_mock.assert_called_once_with('my.mp3')

        metadata = mutagen.mp4.MP4()
        ae = enclosure.AudioEnclosure(None, 'http://example.com/download/mp4/?id=123')
        ae._metadata = metadata

        assert (ae.filename_ext == '.m4a'), \
            "filename_ext should be determined by metadata when URL does not" \
            "provide the filename."

    def test_metadata(self, mocker):
        """
        AudioEnclosure should be able to introspect the file from the URL 
        passed to it to extract basic metadata about the file, such as its 
        format.
        """
        # mock mutagen.File
        MockMutagenFile = mocker.patch('mutagen.File')

        info = types.SimpleNamespace()
        info.length = 60
        info.bitrate = 8
        info.sample_rate = 16

        type(MockMutagenFile.return_value).info = \
            mock.PropertyMock(return_value=info)
        type(MockMutagenFile.return_value).tags = \
            mock.PropertyMock(return_value='foo')

        # mock AudioEnclosure._file to avoid making a bad request
        mock_file = mocker.patch('podstar.enclosure.AudioEnclosure._file', 
            new_callable=mock.PropertyMock,
            return_value=io.BytesIO())

        file_url = 'http://example.com/my.mp3'
        ae = enclosure.AudioEnclosure(None, file_url)

        # ensure that all of our properties work
        assert ae.metadata == MockMutagenFile.return_value
        assert ae.duration == 60
        assert ae.bitrate == 8
        assert ae.sample_rate == 16
        assert ae.url == file_url
        assert ae.tags == 'foo'
        assert ae.info == info

    def test_save(self, mocker):
        """
        AudioEnclosure should allow the file from the URL passed to it to be 
        saved to the local filesystem.
        """
        content = b'Is the outside frame in the trunk wide? (yes!)\n' \
            b'Are the rims big? (what!)\nDo it ride good? (good!)'

        # mock AudioEnclosure._file to avoid making a bad request
        mock_file = mocker.patch('podstar.enclosure.AudioEnclosure._file', 
            new_callable=mock.PropertyMock,
            return_value=io.BytesIO(content))

        ae = enclosure.AudioEnclosure(None, 'http://example.com/my.mp3')

        # seek to some weird cursor position in the buffer
        mock_file.return_value.seek(10)
        
        # attempt to save
        with tempfile.TemporaryFile() as fh:
            ae.save(fh)
            fh.seek(0)

            assert (fh.read() == content), \
                "contents of enclosure should match the contents of dest file"

        assert (mock_file.return_value.tell() == 0), \
            "be kind, please rewind"

    def test_file(self, mocker):
        # TODO(kk): Add this test.
        pass