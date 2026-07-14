import asyncio
import edge_tts

async def main():
    voices = await edge_tts.VoicesManager.create()
    for v in voices.voices:
        if 'es-' in v['Locale']:
            print(f"{v['Name']} - {v['Gender']}")

if __name__ == '__main__':
    asyncio.run(main())
