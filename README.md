# Cyberspace-Bot

Official Discord bot for the Cyberspace cybersecurity club at Slippery Rock University.

## Features

- Welcome messages + onboarding DMs
- Music playback
- Google Calendar meeting list + 24h / 1h reminders
- Curated learning resource library
- Self-assign interest roles (Red / Blue / Hardware / Cloud / Competing)
- Help queue for officers (`!helpme`)
- Lab / VPN / VM status board
- Secret-leak filter + protected announcement channels
- Practice CTF challenges + leaderboard
- Event RSVP / attendance

## Setup

1. Create a venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

2. Install FFmpeg (music):

```bash
brew install ffmpeg
```

3. Create `token.env`:

```env
discord_token=YOUR_BOT_TOKEN
google_calendar_id=primary
```

4. Discord Developer Portal → Bot → enable:
   - Message Content Intent
   - Server Members Intent

5. Invite the bot with permissions to manage roles, manage messages, connect/speak, and send messages.

6. (Optional) Google Calendar reminders:
   - Create an OAuth Desktop client in Google Cloud
   - Enable the Google Calendar API
   - Save the client file as `credentials.json` in the project root
   - Run the bot once and complete the browser consent flow (`calendar_token.json` is created)

7. Run:

```bash
python CyberBot.py
```

## First-run officer checklist

```text
!setchannel #announcements
!setofficers #officers
!roles setup
!onboarding message Welcome to Cyberspace! ...
!onboarding rules #rules
!protect on          (in #announcements)
!reminders on
!status set lab up Ready for Thursday workshop
```

## Command map

| Area | Commands |
| --- | --- |
| Basics | `!clubhelp`, `!ping`, `!online`, `!info`, `!exit` |
| Channels | `!setchannel`, `!setofficers`, `!greet` |
| Music | `!play`, `!pause`, `!resume`, `!skip`, `!stop`, `!queue`, `!np`, `!join`, `!leave` |
| Calendar | `!events`, `!reminders on\|off` |
| Resources | `!resources [topic]`, `!resourceadd`, `!resourceremove` |
| Roles | `!roles`, `!roles setup` |
| Help queue | `!helpme`, `!helplist`, `!helpdone` |
| Infra | `!status`, `!status set <lab\|vpn\|vms> <up\|down\|...> [note]` |
| Moderation | `!slowmode`, `!protect`, `!secretfilter` |
| Onboarding | `!onboarding ...` |
| CTF | `!challenge ...`, `!leaderboard` |
| RSVP | `!rsvp ...` |

Guild settings are stored in `data/store.json`.
