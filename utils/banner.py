from art import *

def generate_banner():
  # added "powered by Yack" to the bottom of the art
  Art=text2art("Hacking for Good","random")
  # get the wide of the art
  width=len(Art.split("\n")[0])
  dynamic_line = '-' * width
  print("")
  print(dynamic_line)
  print(Art)
  # print text centered with the art
  print(' ' * (width // 2 - 15) + 'Powered by Yack. Made with 🫶.')
  print(' ' * (width // 2 - 15) + '------ https://yack.one ------' + "\n")
  print(dynamic_line + "\n")

# generate_banner()