import os
import warnings
import logging
import cv2
import pytesseract
import re
import time
from ultralytics import YOLO
from gpiozero import OutputDevice
from time import sleep

# --- AI & CAMERA SETUP ---
os.environ["QT_QPA_PLATFORM"] = "xcb"
warnings.filterwarnings("ignore", message=".*pin_memory.*")
logging.getLogger("ultralytics").setLevel(logging.ERROR)
model = YOLO('license-plate-finetune-v1n.pt')
cap = cv2.VideoCapture(0)

# --- MOTOR SETUP ---
in1 = OutputDevice(25)
in2 = OutputDevice(16)
in3 = OutputDevice(20)
in4 = OutputDevice(12)
stap_volgorde = [[1,0,0,1],[1,0,0,0],[1,1,0,0],[0,1,0,0],[0,1,1,0],[0,0,1,0],[0,0,1,1],[0,0,0,1]]

def open_garage():
    print("✅ Toegang verleend! Garagepoort opent...")
    for i in range(512):
        for halve_stap in range(8):
            in1.value = stap_volgorde[halve_stap][0]
            in2.value = stap_volgorde[halve_stap][1]
            in3.value = stap_volgorde[halve_stap][2]
            in4.value = stap_volgorde[halve_stap][3]
            sleep(0.001)
    in1.off(); in2.off(); in3.off(); in4.off()
    print("Garagepoort is open.")

# --- OCR FUNCTIES ---
def optimize_for_ocr(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def perform_filtered_ocr(processed_crop):
    custom_config = r'--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    text = pytesseract.image_to_string(processed_crop, config=custom_config).strip()
    clean_text = ''.join(filter(str.isalnum, text)).upper()
    if not clean_text: return None
    
    first_char = clean_text[0]
    if first_char in ['I', 'L', '|']: first_char = '1'
    if first_char == 'Z': first_char = '2'
    if first_char in ['B', 'H']: first_char = '' 
    
    normalized_text = first_char + clean_text[1:]
    if re.match(r"^[12][A-Z0-9]{6}$", normalized_text):
        return normalized_text
    return None

# --- HOOFDPROGRAMMA ---
print("Systeem gestart. Hou een nummerplaat voor de camera.")
print("Druk op 'Ctrl + C' om te stoppen.")

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        display_frame = frame.copy()
        results = model(frame, stream=True, conf=0.5, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_roi = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
                
                if plate_roi.size > 0:
                    processed_plate = optimize_for_ocr(plate_roi)
                    plate_text = perform_filtered_ocr(processed_plate)
                    
                    if plate_text:
                        color = (0, 255, 0)
                        label = f"MATCH: {plate_text}"
                        print(f"Nummerplaat gelezen: {plate_text}")
                        cv2.imwrite("live_camera.jpg", display_frame) # Bewaar bewijsfoto
                        
                        # Start de motor
                        open_garage()
                        
                        # Wacht 5 seconden na het openen, anders blijft de AI hem direct opnieuw scannen
                        print("Wachten op auto om binnen te rijden...")
                        time.sleep(5) 
                        print("Klaar voor de volgende scan.")
                    else:
                        color = (0, 0, 255)
                        label = "Genegeerd"
                        
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(display_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.imwrite("wat_de_ai_ziet.jpg", processed_plate)
                    
        cv2.imwrite("live_camera.jpg", display_frame)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSysteem gestopt.")
finally:
    cap.release()