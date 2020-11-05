import re
from typing import Union

from django.contrib.sessions.backends.base import SessionBase
from django.core.files import File

from pegasus.settings import MEDIA_ROOT, MEDIA_URL
from reels.models import User, SessionClip, SessionAudio
import time
from os import listdir


# === Users ===

# Login a user
def session_login(session: SessionBase, user: User) -> None:
    session['user_data'] = user.__dict__


# Logout a user
def session_logout(session: SessionBase) -> None:
    session.pop('user_data')


# Check if a user is already logged in
def session_is_logged_in(session: SessionBase) -> bool:
    return 'user_data' in session


# Get the User of a session, assuming one exists.
def session_get_user(session: SessionBase) -> User:
    d = session['user_data']
    return User(d['user_name'], d['password'], d['email'], d['user_id'],
                d['created'], d['last_online'], d['verified'])


def session_context(session: SessionBase) -> dict:
    context = {}
    if session_is_logged_in(session):
        context['user_data'] = session['user_data']
    context['uploaded_clips'] = get_session_clips(session.session_key)
    context['uploaded_audio'] = get_session_audio(session.session_key)
    return context


# === Uploading ===

# Uploads a clip to media folder
# MEDIA format: /media/reels-clip-{session_key}-{epoch_time_in_seconds}-{index}.mp4
# This assumes mp4 format
def upload_session_clips(session_key: str, files: list) -> list:
    clips = []
    time_sec = int(time.time())
    for i in range(len(files)):
        destination_location = '{}reels-clip-{}-{}-{}.{}'.format(MEDIA_ROOT, session_key, time_sec, i, 'mp4')
        with open(destination_location, 'wb+') as destination:
            for chunk in files[i].chunks():
                destination.write(chunk)
        clips.append(SessionClip(destination_location, session_key, {}))
    return clips


# Gets a list of SessionClips associated with a session
def get_session_clips(session_key: str) -> list:
    # TODO use cached dictionary for this instead for efficiency
    regex = r'^reels-clip-.{32}-[0-9]{10}-[0-9]{0,5}\.[a-zA-Z0-9]{0,10}$'
    return [SessionClip(MEDIA_ROOT + f, session_key, {}) for f in listdir(MEDIA_ROOT)
            if re.match(regex, f.lower())
            and f[11:43] == session_key]


# Uploads an audio file
# MEDIA format: /media/reels-audio-{session_key}.mp3
# This assumes mp3 format
def upload_session_audio(session_key: str, file: File) -> SessionAudio:
    destination_location = '{}reels-audio-{}-{}.{}'.format(MEDIA_ROOT, session_key, int(time.time()), 'mp3')
    with open(destination_location, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return SessionAudio(destination_location, session_key, {})


# Gets the audio associated with a session
def get_session_audio(session_key: str) -> Union[SessionAudio, None]:
    regex = r'^reels-audio-.{32}-[0-9]{10}\.[a-zA-Z0-9]{0,10}$'
    for f in listdir(MEDIA_ROOT):
        if (re.match(regex, f)
                and f[12:44] == session_key):
            return SessionAudio(MEDIA_ROOT + f, session_key, {})
    return None


# Upload a video to media folder
def save_session_video_location(session_key: str, video_id: str) -> str:
    return '{}reels-video-{}-{}.{}'.format(MEDIA_ROOT, session_key, video_id, 'mp4')
