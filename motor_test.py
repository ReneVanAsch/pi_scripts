from gpiozero import OutputDevice
from time import sleep

# Configuratie met vrije, onbeveiligde GPIO pinnen
in1 = OutputDevice(25) # Fysieke pin 22
in2 = OutputDevice(16) # Fysieke pin 36 (aangepast)
in3 = OutputDevice(20) # Fysieke pin 38 (aangepast)
in4 = OutputDevice(12) # Fysieke pin 32

stap_volgorde = [
    [1,0,0,1],
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1]
]

print("De garagepoort gaat open (motor draait)...")

# 512 keer deze reeks uitvoeren = precies 1 volledige draai
for i in range(512):
    for halve_stap in range(8):
        in1.value = stap_volgorde[halve_stap][0]
        in2.value = stap_volgorde[halve_stap][1]
        in3.value = stap_volgorde[halve_stap][2]
        in4.value = stap_volgorde[halve_stap][3]
        sleep(0.001)

in1.off()
in2.off()
in3.off()
in4.off()

print("Klaar!")