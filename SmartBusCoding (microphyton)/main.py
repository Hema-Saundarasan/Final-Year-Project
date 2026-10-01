#-----------HEMA SAUNDARASAN----------------#
#--------------52224123036_-----------------#
#-------------------------main.py-------------------------------##
import time
from machine import Pin, SPI, SoftI2C, SoftSPI, PWM, ADC
from mfrc522 import MFRC522
from i2c_lcd import I2cLcd
from ssd1306 import SSD1306_SPI
import dht
import network
import urequests

# ================= RFID =================
spi = SPI(1, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi, Pin(5, Pin.OUT))

# ================= LCD =================
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
lcd = I2cLcd(i2c, 0x27, 2, 16)

# ================= OLED =================
spi_oled = SoftSPI(baudrate=1000000, polarity=0, phase=0,
                   sck=Pin(14), mosi=Pin(13), miso=Pin(12))
oled = SSD1306_SPI(128, 64, spi_oled, dc=Pin(17), res=Pin(27), cs=Pin(26))

# ================= BUTTONS =================
btnA = Pin(32, Pin.IN)
btnB = Pin(35, Pin.IN)
btnC = Pin(2, Pin.IN, Pin.PULL_UP)

# ================= BUZZER =================
buzzer = Pin(16, Pin.OUT)

# ================= SERVO =================
servo = PWM(Pin(33), freq=50)

# ================= DHT11 =================
dht_sensor = dht.DHT11(Pin(25))

# ================= MQ2 =================
mq2 = ADC(Pin(34))
mq2.atten(ADC.ATTN_11DB)

# ================= USERS =================
DRIVER_UID = "E9BA326D0C"
AUTHORIZED = {
    "37C61D49A5": 1,
    "250D9FE057": 201,
    "07C8059F55": 251,
    "299194113D" : 258,
    "FD64F4EC81": 322
}
LCD_NAMES = {1: "Student 001", 201: "Student 201", 251: "Student 251", 258:"Student 258", 322: "Student 322"}

attendance = []
rejected = 0
route = 0
route_name = ""
temp_alert = False
gas_alert = False
last_upload = 0

# ================= THINGSPEAK =================

# Environment Channel
WRITE_API_ENV = "5XFHAJWQFIMYMH5F"

# Attendance Channel
WRITE_API_ATT = "F9EDOZV0NNQESNOW"


# ================= TELEGRAM CONFIGURATION =================
BOT_TOKEN = "8838140634:AAG4T6DhIliRmJSnWTr2FdM7dDKI3-2jPGk"
CHAT_ID = "-1003739885614"

# Local student data database matching script.js
STUDENT_DB = {
    "1": "Muhammad Ali",
    "201": "JeyaKumar Saravanan",
    "251": "Joseph Vijay",
    "258": "Sri",
    "322": "Adriana Sarah Binti Ahmad Faiza"
}

# ================= TELEGRAM FUNCTION =================
def send_telegram_alert(student_id, route_code, status_code):

    try:

        student_name = STUDENT_DB.get(str(student_id), "Unknown Student")

        if route_code == 1:
            route_text = "Home to School"
        elif route_code == 2:
            route_text = "School to Home"
        else:
            route_text = "Unknown Route"

        if status_code == 1:
            status_text = "Present"
        elif status_code == 2:
            status_text = "Duplicate Entry"
        elif status_code == 3:
            status_text = "Unauthorized Access"
        elif status_code == 9:
            status_text = "Ride Ended"
        else:
            status_text = "Unknown"

        message = (
            "SMART BUS NOTIFICATION\n\n"
            "Name: {}\n"
            "ID: {}\n"
            "Route: {}\n"
            "Status: {}"
        ).format(
            student_name,
            student_id,
            route_text,
            status_text
        )

        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        print("Sending Telegram Notification...")

        response = urequests.post(url, json=payload)

        print("Telegram Response:")
        print(response.text)

        response.close()

        print("Telegram Notification Sent")

    except Exception as e:
        print("Telegram Error:", e)
# ================= FUNCTIONS =================

def connect_wifi():
    ssid = "RMHPS-2.4"
    password = "0530252218"
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False); time.sleep(1)
    wlan.active(True); time.sleep(1)
    print("Connecting WiFi...")
    wlan.connect(ssid, password)
    timeout = 15; start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            print("WiFi Connection Failed"); return
        time.sleep(0.5)
    print("WiFi Connected"); print(wlan.ifconfig())

def lcd_message(line1="", line2=""):
    lcd.clear(); lcd.putstr(line1 + "\n" + line2)

def beep(times):
    for i in range(times):
        buzzer.on(); time.sleep(0.2)
        buzzer.off(); time.sleep(0.2)

def open_door(): servo.duty(40)
def close_door(): servo.duty(115)
    
def upload_environment(temp, hum, gas):
    url = (
        f"https://api.thingspeak.com/update"
        f"?api_key={WRITE_API_ENV}"
        f"&field1={temp}"
        f"&field2={hum}"
        f"&field3={gas}"
    )

    try:
        response = urequests.get(url)
        print("Environment Response:", response.text)
        response.close()

    except Exception as e:
        print("Environment Upload Failed", e)
        
def upload_attendance(student, route, status_code, present_count, rejected_count):

    url = (
        f"https://api.thingspeak.com/update"
        f"?api_key={WRITE_API_ATT}"
        f"&field4={student}"
        f"&field5={route}"
        f"&field6={status_code}"
        f"&field7={present_count}"
        f"&field8={rejected_count}"
    )

    try:
        response = urequests.get(url)

        print("Attendance Response:", response.text)

        response.close()

    except Exception as e:
        print("Attendance Upload Failed", e)
    
def get_uid():
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            return "".join("{:02X}".format(x) for x in uid)
    return None
def send_ride_started(route_code):

    if route_code == 1:
        route_text = "Home to School"
    elif route_code == 2:
        route_text = "School to Home"
    else:
        route_text = "Unknown Route"

    message = (
        "RIDE STARTED\n\n"
        "Route: {}\n"
        "Status: Ride Started"
    ).format(route_text)
    
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        
        payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
        response = urequests.post(url, json=payload)
        
        print("Ride Start Response:")
        print(response.text)

        response.close()

    except Exception as e:
        print("Ride Start Error:", e)
        
def send_ride_summary(route_code, total_students):

    if route_code == 1:
        route_text = "Home to School"
    elif route_code == 2:
        route_text = "School to Home"
    else:
        route_text = "Unknown Route"

    message = (
        "RIDE ENDED SAFELY\n\n"
        "Ride Summary\n\n"
        "Ride: Ride Ended \n\n"
        "Route: {}\n\n"
        "Total Students: {}"
    ).format(
        route_text,
        total_students
    )

    url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = urequests.post(url, json=payload)
        response.close()
        print("Ride Summary Notification Sent")
        print(response.text)
    except Exception as e:
        print("Telegram Error:", e)

def show_environment():
    global temp_alert, gas_alert, last_upload
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        gas = mq2.read()
        if time.time() - last_upload >= 15:
            upload_environment(temp, hum, gas)
            last_upload = time.time()
        if temp >= 38 and not temp_alert:
            temp_alert = True; beep(5)
            lcd_message("HIGH TEMP!", str(temp) + " C"); time.sleep(3)
        elif temp < 32: temp_alert = False
        if gas >= 500 and not gas_alert:
            gas_alert = True; beep(5)
            lcd_message("! DANGER:", "AIR !"); time.sleep(3)
        elif gas < 500: gas_alert = False
        oled.fill(0)
        oled.text("SMART BUS", 0, 0)
        oled.text(f"Temp:{temp}C", 0, 15)
        oled.text(f"Hum:{hum}%", 0, 30)
        oled.text(f"Gas:{gas}", 0, 45)
        oled.show()
    except:
        oled.fill(0); oled.text("Sensor Error", 0, 0); oled.show()

def scan_driver():
    while True:
        lcd_message("Scan Driver's", "Card")
        uid = get_uid()
        if uid:
            print("Detected:", uid)
            if uid == DRIVER_UID:
                print("Driver Verified"); beep(1)
                open_door(); time.sleep(3); close_door()
                lcd_message("Driver", "Verified")
                oled.fill(0); oled.text("Driver Verified", 0, 20); oled.show()
                time.sleep(2); return
            else:
                lcd_message("Invalid", "Driver"); beep(3); time.sleep(2)

def select_route():
    global route, route_name
    lcd_message("Press A/B", "Select Route")
    
    while True:
        
        if btnA.value() == 1:
            route = 1
            route_name = "Home to School"
            lcd_message(route_name, "Selected");
            send_ride_started(route)
            time.sleep(2)
            return
        
        if btnB.value() == 1:
            route = 2
            route_name = "School to Home"
            lcd_message(route_name, "Selected")
            send_ride_started(route)
            time.sleep(2)
            return

def ride_session():
    global rejected
    lcd_message("Ride Started", route_name); time.sleep(2)
    while True:
        show_environment()
        if btnC.value() == 1: return
        uid = get_uid()
        if uid:
            print("Student UID:", uid)
            if uid in AUTHORIZED:
                student_num = AUTHORIZED[uid]; display_name = LCD_NAMES[student_num]
                if uid not in attendance:
                    attendance.append(uid)
                    lcd_message("Welcome", display_name)
                    open_door(); time.sleep(3); close_door()
                    upload_attendance(student_num, route, 1, len(attendance), rejected)
                    send_telegram_alert(student_num, route, 1)
                else:
                    lcd_message("Duplicate", "Entry"); beep(2); time.sleep(2)
                    rejected += 1
                    upload_attendance(student_num, route, 2, len(attendance), rejected)
                    send_telegram_alert(student_num, route, 2)
            else:
                lcd_message("Unauthorized", "Access"); beep(3); time.sleep(2)
                rejected += 1
                upload_attendance(404, route, 3, len(attendance), rejected)
                send_telegram_alert(404, route, 3)
        time.sleep(0.1)

def ride_summary():
    total = len(attendance)
    lcd_message("Ride Ended", ""); time.sleep(2)
    oled.fill(0)
    oled.text("RIDE SUMMARY", 0, 0)
    oled.text("Route:", 0, 15); oled.text(route_name, 0, 25)
    oled.text("Present:" + str(total), 0, 40)
    oled.text("Reject:" + str(rejected), 0, 55); oled.show()
    print("\n===== SUMMARY =====")
    print("Route:", route_name); print("Present:", total); print("Rejected:", rejected)
    for uid in attendance:
        if uid in AUTHORIZED:
            print(LCD_NAMES[AUTHORIZED[uid]])
    # Upload ride completed marker
    print("Waiting before summary upload...")
    time.sleep(6)
    upload_attendance(
        0,
        route,
        9,
        total,
        rejected
    )
    send_ride_summary(route, total)
    print("Summary uploaded")
    time.sleep(6)

def reset_system():
    global attendance, rejected, route, route_name
    attendance = []
    rejected = 0
    route = 0
    route_name = ""

# ================= EXECUTION LOOP =================
connect_wifi()

while True:
    reset_system()
    scan_driver()
    select_route()
    ride_session()
    ride_summary()
