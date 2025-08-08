from lib.ref.loader import find_audio_by_char_name
urls = find_audio_by_char_name(角色名, limit=1)
print(urls)
# 或英文
urls = find_audio_by_char_name("franka", limit=5)