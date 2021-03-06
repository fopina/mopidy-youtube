from __future__ import unicode_literals

import mock

import pafy

import pytest

import vcr

from mopidy_youtube import backend
from mopidy_youtube.backend import YouTubeLibraryProvider


@pytest.yield_fixture
def pafy_mock():
    patcher = mock.patch.object(backend, 'pafy', spec=pafy)
    yield patcher.start()
    patcher.stop()


@pytest.fixture
def pafy_mock_with_video(pafy_mock):
    video_mock = pafy_mock.new.return_value
    video_mock.bigthumb = 'big thumb'
    video_mock.bigthumbhd = 'big thumb in hd'
    video_mock.getbestaudio.return_value.url = 'http://example.com/'
    video_mock.length = 2000
    video_mock.title = 'a title'
    video_mock.videoid = 'a video id'

    return pafy_mock


@vcr.use_cassette('tests/fixtures/youtube_playlist_resolve.yaml')
def test_playlist_resolver(pafy_mock_with_video):
    videos = backend.resolve_playlist('PLOxORm4jpOQfMU7bpfGCzDyLropIYEHuR')

    assert len(videos) == 104


@vcr.use_cassette('tests/fixtures/youtube_search.yaml')
def test_search_yt(pafy_mock_with_video):
    videos = backend.search_youtube('chvrches')

    assert len(videos) == 15


@vcr.use_cassette('tests/fixtures/resolve_track.yaml')
def test_resolve_track(pafy_mock_with_video):
    video = backend.resolve_track('C0DPdy98e4c')

    assert video


@vcr.use_cassette('tests/fixtures/resolve_track_failed.yaml')
def test_resolve_track_failed(pafy_mock):
    pafy_mock.new.side_effect = Exception('Removed')

    video = backend.resolve_track('unknown')

    assert not video


@vcr.use_cassette('tests/fixtures/resolve_track_stream.yaml')
def test_resolve_track_stream(pafy_mock_with_video):
    video = backend.resolve_track('C0DPdy98e4c', stream=True)

    assert video


@vcr.use_cassette('tests/fixtures/resolve_video_track_stream.yaml')
def test_resolve_video_track_stream(pafy_mock_with_video):
    video = backend.resolve_track('youtube:video/a title.a video id',
                                  stream=True)

    assert video
    assert video.uri == "http://example.com/"


@vcr.use_cassette('tests/fixtures/lookup_video_uri.yaml')
def test_lookup_video_uri(caplog):
    provider = YouTubeLibraryProvider(mock.PropertyMock())

    track = provider.lookup(backend.video_uri_prefix +
                            '/a title.C0DPdy98e4c')

    assert 'Need 11 character video id or the URL of the video.' \
           not in caplog.text()

    assert track

    assert track[0].uri == backend.video_uri_prefix + \
        '/TEST VIDEO.C0DPdy98e4c'
