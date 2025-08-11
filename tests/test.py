from lib.ref.loader import find_audio_with_text_by_char_name, find_audio_by_char_name
# urls = find_audio_with_text_by_char_name("银灰", limit=1)#查询的
# #返回的['/Users/ycc/workspace/Chat/ArknightsAutoDubbing/lib/ref/voices/char_1028_texas2_CN_007.wav']
# print(urls)
urls = find_audio_with_text_by_char_name("星熊", limit=1)#查询的
#返回的['/Users/ycc/workspace/Chat/ArknightsAutoDubbing/lib/ref/voices/char_1028_texas2_CN_007.wav']
print(urls)
# # 或英文
# urls = find_audio_with_text_by_char_name("franka", limit=1)
# print(urls)

