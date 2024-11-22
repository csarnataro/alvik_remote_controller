from modulino import ModulinoBuzzer
from time import sleep_ms

tempo = 95
wholenote = int((60000 * 4) / tempo)

divider = 0
noteDuration = 0

def play_tune(tune_function):

  # PACMAN
  melody = [
    (ModulinoBuzzer.NOTES["B4"], 16),
    (ModulinoBuzzer.NOTES["B5"], 16),
    (ModulinoBuzzer.NOTES["FS5"], 16),
    (ModulinoBuzzer.NOTES["DS5"], 16),
    (ModulinoBuzzer.NOTES["B5"], 32),
    (ModulinoBuzzer.NOTES["FS5"], -16),
    (ModulinoBuzzer.NOTES["DS5"], 8),
    
    (ModulinoBuzzer.NOTES["C5"], 16),
    (ModulinoBuzzer.NOTES["C6"], 16),
    (ModulinoBuzzer.NOTES["G6"], 16),
    (ModulinoBuzzer.NOTES["E6"], 16),
    (ModulinoBuzzer.NOTES["C6"], 32),
    (ModulinoBuzzer.NOTES["G6"], -16),
    (ModulinoBuzzer.NOTES["E6"], 8),
    
    (ModulinoBuzzer.NOTES["B4"], 16),
    (ModulinoBuzzer.NOTES["B5"], 16),
    (ModulinoBuzzer.NOTES["FS5"], 16),
    (ModulinoBuzzer.NOTES["DS5"], 16),
    (ModulinoBuzzer.NOTES["B5"], 32),
    (ModulinoBuzzer.NOTES["FS5"], -16),
    (ModulinoBuzzer.NOTES["DS5"], 8),
    
    (ModulinoBuzzer.NOTES["DS5"], 32),
    (ModulinoBuzzer.NOTES["E5"], 32),
    (ModulinoBuzzer.NOTES["F5"], 32),
    (ModulinoBuzzer.NOTES["F5"], 32),
    (ModulinoBuzzer.NOTES["FS5"], 32),
    (ModulinoBuzzer.NOTES["G5"], 32),
    (ModulinoBuzzer.NOTES["G5"], 32),
    (ModulinoBuzzer.NOTES["GS5"], 32),
    (ModulinoBuzzer.NOTES["A5"], 16),
    (ModulinoBuzzer.NOTES["B5"], 8),    
  ]

  for note, divider in melody:
      if divider > 0:
        noteDuration = int(wholenote / divider)
      elif divider < 0:
        noteDuration = -1 * int(wholenote / divider)
        noteDuration *= 1.5
    
      tune_function(note, int(noteDuration * 0.9), blocking=True)
      tune_function(ModulinoBuzzer.NOTES["REST"], int(noteDuration * 0.1), blocking=True)
  
if (__name__ == "__main__"):
  from machine import I2C, Pin
  buzzer = ModulinoBuzzer(I2C(0, scl=Pin(12, Pin.OUT), sda=Pin(11, Pin.OUT)))
  play_tune(buzzer.tone)



  
