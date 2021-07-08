import requests
import os

INTERVIEW_PASSED = 'https://static.wikia.nocookie.net/dota2_gamepedia/images/0/0f/Music_TheFatRat_Warrior_Songs_respawn.mp3'

INTERVIEW_FAILED = 'https://static.wikia.nocookie.net/dota2_gamepedia/images/f/fe/Music_TheFatRat_Warrior_Songs_dire_lose.mp3'

with open('interview-ok.mp3', 'wb') as o:
    o.write(requests.get(INTERVIEW_PASSED).content)

with open('interview-fail.mp3', 'wb') as o:
    o.write(requests.get(INTERVIEW_FAILED).content)

os.system("ffmpeg-normalize interview-ok.mp3 -t-11 -nt rms -ext mkv")
os.unlink("interview-ok.mp3")
os.rename("normalized/interview-ok.mkv", "interview-ok.mkv")
os.system("ffmpeg-normalize interview-fail.mp3 -t-11 -nt rms -ext mkv")
os.unlink("interview-fail.mp3")
os.rename("normalized/interview-fail.mkv", "interview-fail.mkv")
