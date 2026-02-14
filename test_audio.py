import pyttsx3
import threading
import time

print("=" * 60)
print("AUDIO SYSTEM TEST")
print("=" * 60)

# Test 1: Basic initialization
print("\n1. Testing TTS engine initialization...")
try:
    engine = pyttsx3.init()
    print("   ✓ Engine initialized successfully")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    exit(1)

# Test 2: Get voices
print("\n2. Available voices:")
try:
    voices = engine.getProperty('voices')
    for i, voice in enumerate(voices):
        print(f"   {i}: {voice.name}")
    print(f"   ✓ Found {len(voices)} voices")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 3: Set properties
print("\n3. Setting voice properties...")
try:
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    print("   ✓ Properties set successfully")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 4: Simple speech
print("\n4. Testing simple speech...")
try:
    engine.say("Audio test successful")
    engine.runAndWait()
    print("   ✓ Speech test passed")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 5: Threaded speech
print("\n5. Testing threaded speech...")
def speak_threaded(text):
    def tts():
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"   ✗ Thread error: {e}")
    
    thread = threading.Thread(target=tts, daemon=True)
    thread.start()
    thread.join(timeout=5)

try:
    speak_threaded("Threading test")
    print("   ✓ Threaded speech works")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 6: Word pronunciation
print("\n6. Testing word pronunciation...")
test_words = ["HELLO", "WORLD", "TEST"]
for word in test_words:
    try:
        print(f"   Speaking: {word}")
        engine.say(word)
        engine.runAndWait()
        time.sleep(0.5)
    except Exception as e:
        print(f"   ✗ Failed on '{word}': {e}")

print("\n" + "=" * 60)
print("AUDIO TEST COMPLETE")
print("=" * 60)
print("\nIf you heard all the words, audio is working correctly!")
print("If not, check:")
print("  - System volume is not muted")
print("  - Speakers/headphones are connected")
print("  - Audio drivers are installed")
print("  - Try different voice (change voice index)")
