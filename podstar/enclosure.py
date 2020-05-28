import os
import tempfile
from urllib.parse import urlparse

import mutagen
import mutagen.aac
import mutagen.aiff
import mutagen.monkeysaudio
import mutagen.asf
import mutagen.dsf
import mutagen.flac
import mutagen.mp3
import mutagen.mp4
import mutagen.musepack
import mutagen.oggflac
import mutagen.oggopus
import mutagen.oggspeex
import mutagen.oggtheora
import mutagen.oggvorbis
import mutagen.optimfrog
import mutagen.trueaudio
import mutagen.wavpack

from podstar import stream


MUTAGEN_TYPE_EXTENSIONS = {
    mutagen.aac.AAC: '.aac',
    mutagen.aiff.AIFF: '.aiff',
    mutagen.monkeysaudio.MonkeysAudio: '.ape',
    mutagen.asf.ASF: '.wma',
    mutagen.dsf.DSF: '.dsf',
    mutagen.flac.FLAC: '.flac',
    mutagen.mp3.MP3: '.mp3',
    mutagen.mp4.MP4: '.m4a',
    mutagen.musepack.Musepack: '.mpc',
    mutagen.oggflac.OggFLAC: '.ogg',
    mutagen.oggopus.OggOpus: '.ogg',
    mutagen.oggspeex.OggSpeex: '.ogg',
    mutagen.oggtheora.OggTheora: '.ogg',
    mutagen.oggvorbis.OggVorbis: '.ogg',
    mutagen.optimfrog.OptimFROG: '.ofr',
    mutagen.trueaudio.TrueAudio: '.tta',
    mutagen.wavpack.WavPack: '.wv',
}


class AudioEnclosure(object):
    """Enclosure wraps an audio file associated with a podcast episode.

    Notes:
        Often, audio file metadata can be extracted from the first few hundred 
        bytes of a file -- this means that we don't need to actually fetch the 
        entire file to get useful information such as its codec, duration, 
        bitrate, etc.

        Working with AudioEnclosures is not intrinsically thread-safe due to 
        the use of a shared instance of the underlying file.
    """

    FS_WRITE_THRESHOLD = 131072 # 128kB in-memory buffer
    REMOTE_READ_TIMEOUT = 10

    def __init__(self, feed, url):
        self._feed = feed
        self._url = url
        self._metadata = None
        self._cache_fh = None

        self._filename = os.path.basename(urlparse(url).path)
        self._filename_ext = None

    @property
    def _file(self):
        if self._cache_fh is None:
            resp = self._feed._request(
                'GET', self._url, stream=True, allow_redirects=True)
            resp.raw.decode_content = True
            buffer = tempfile.SpooledTemporaryFile(
                max_size=self.FS_WRITE_THRESHOLD)
            self._cache_fh = stream.Seeker(resp.raw, buffer=buffer)
        return self._cache_fh

    def save(self, dest):
        try:
            self._file.seek(0)
            return dest.write(self._file.read())
        finally:
            self._file.seek(0)

    @property
    def metadata(self):
        if self._metadata is None:
            try:
                self._file.seek(0)
                self._metadata = mutagen.File(self._file)
            finally:
                self._file.seek(0)
        return self._metadata

    @property
    def filename(self):
        return self._filename

    @property
    def filename_ext(self):
        if self._filename_ext is None:
            if len(self._filename) == 0:
                self._filename_ext = MUTAGEN_TYPE_EXTENSIONS.get(
                    self.metadata.__class__, None)
            else:
                _, self._filename_ext = os.path.splitext(self.filename)

        return self._filename_ext

    @property
    def info(self):
        return self.metadata.info

    @property
    def tags(self):
        return self.metadata.tags

    @property
    def url(self):
        return self._url

    @property
    def duration(self):
        return self.info.length

    @property
    def bitrate(self):
        return self.info.bitrate

    @property
    def sample_rate(self):
        return self.info.sample_rate