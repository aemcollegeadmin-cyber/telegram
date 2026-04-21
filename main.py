from telethon import TelegramClient
from flask import Flask, jsonify
import asyncio
import re
import random
import os

API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH', '')
PORT = int(os.environ.get('PORT', '5055'))

CHANNELS = [
    'robota_ua',
    'vakansii_ukraine',
    'work_ukraine',
    'rabota_ua_vakansii',
    'ukr_jobs',
    'jobs_ukraine_ua',
    'robota_bez_dosvidu',
    'vakansii_lviv',
    'kyiv_jobs',
    'rabota_kharkiv',
]

app = Flask(__name__)

PHONE_REGEX = re.compile(
    r'(\+?38)?[\s\-]?\(?(0\d{2})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
)
SALARY_REGEX = re.compile(
    r'(1[0-5][\s]?000|[5-9][\s]?000)[\s]*(грн|uah|₴)', re.IGNORECASE
)

# Читаємо сесію з файлу який є в репо
client = TelegramClient('session', API_ID, API_HASH)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/fetch_jobs')
def fetch_jobs():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(get_jobs())
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        loop.close()

async def get_jobs():
    if not client.is_connected():
        await client.connect()

    results = []
    seen = set()

    for channel in CHANNELS:
        try:
            messages = await client.get_messages(channel, limit=100)
            for msg in messages:
                if not msg.text:
                    continue

                text = msg.text
                phone_match = PHONE_REGEX.search(text)
                if not phone_match:
                    continue

                phone = phone_match.group(0).strip()
                salary_match = SALARY_REGEX.search(text)
                salary = salary_match.group(0) if salary_match else 'не вказано'

                url = f'https://t.me/{channel}/{msg.id}'
                if url in seen:
                    continue
                seen.add(url)

                snippet = text[:400].replace('\n', ' ')
                title = text[:60].strip() + '...'

                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'phone': phone,
                    'salary': salary,
                    'source': f't.me/{channel}',
                })

        except Exception as e:
            print(f'Помилка каналу {channel}: {e}')
            continue

    random.shuffle(results)
    return results[:15]

async def start_client():
    await client.connect()
    if not await client.is_user_authorized():
        print('ПОМИЛКА: сесія не авторизована!')
    else:
        print('Telethon підключено успішно!')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_client())
    app.run(host='0.0.0.0', port=PORT)
