import RPi.GPIO as GPIO
import time
import logging
import subprocess
from pathlib import Path
from collections import deque
import sys
import traceback

# Constants
__CurrentDir = Path(__file__).resolve().parent
GPIO_PIN = 12
PWM_FREQ = 20  # Hz
LOG_FILE = __CurrentDir / "fan_control.log"
MAX_LOG_LINES = 100
_SleepTime = 15  # seconds, can be changed

# Global PWM instance
pwm = None

# Setup logging
def setup_logger():
    logger = logging.getLogger("FanControl")
    logger.setLevel(logging.INFO)

    # Log to file
    file_handler = logging.FileHandler(LOG_FILE)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)

    # Add both handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Trim log file to only keep the latest N lines
def trim_log_file():
    if not LOG_FILE.exists():
        return
    with LOG_FILE.open("r") as f:
        lines = deque(f, maxlen=MAX_LOG_LINES)
    with LOG_FILE.open("w") as f:
        f.writelines(lines)

# Load values from external files using __CurrentDir
def load_value(filename):
    try:
        filepath = __CurrentDir / filename
        return float(filepath.read_text().strip())
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return 0.0

# Read current temperature from vcgencmd (Raspberry Pi)
def get_current_temp():
    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        temp_str = output.strip().replace("temp=", "").replace("'C", "")
        temp_value = float(temp_str)
        logger.info(f"Temp ↪ {temp_value}°C")
        return temp_value
    except Exception as e:
        logger.error(f"Error reading temperature: {e}")
        return 100

# GPIO Setup
def setup_gpio():
    global pwm
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(GPIO_PIN, PWM_FREQ)
    pwm.start(0)
    return pwm

# Release GPIO and PWM resources safely
def release_resources():
    try:
        if pwm:
            pwm.stop()
        GPIO.cleanup()
        logger.info("GPIO and PWM released safely.")
    except Exception as e:
        logger.error(f"Error during GPIO cleanup: {e}")

# Functional fan control
def calculate_final_pwm(current_temp, force_value, upper_thres, lower_thres, fan_ctl, prev_pwm):
    if 0 < force_value <= 100:
        return force_value
    
    mid_temp = (upper_thres+lower_thres)/2
    
    if force_value == 0:
        if current_temp > upper_thres:
            return fan_ctl
        elif current_temp > mid_temp:
            return 0.8*fan_ctl
        elif current_temp > lower_thres:
            return 0.4*fan_ctl
        else:
            return 0
    return prev_pwm

# Functional fan control
# def calculate_final_pwm(current_temp, force_value, upper_thres, lower_thres, fan_ctl, prev_pwm):
#     if 0 < force_value <= 100:
#         return force_value
#     if current_temp < lower_thres:
#         return 0
#     elif current_temp > upper_thres:
#         return 100
#     else:
#         return 50

# Turn on the fan
def turn_on(pwm, value):
    pwm.ChangeDutyCycle(value)
    logger.info(f"Final [ON {value}%]")

# Turn off the fan
def turn_off(pwm):
    pwm.ChangeDutyCycle(0)
    logger.info("Final: [OFF]")

# Main loop
def main():
    logger.info("Enter main()")
    logger.info("Create pwm (from setup_gpio())")
    pwm = setup_gpio()
    prev_pwm = 0

    while True:
        try:
            logger.info("Checking...")

            current_temp = get_current_temp()

            force_value = load_value("__ForceValue.txt")
            upper_thres = load_value("__UpperThresTemp.txt")
            lower_thres = load_value("__LowerThresTemp.txt")

            logger.info(f"► {force_value} ▼ {lower_thres} ▲ {upper_thres}")

            fan_ctl = 100  # You can load this from a config file if needed

            final_pwm = calculate_final_pwm(current_temp, force_value, upper_thres, lower_thres, fan_ctl, prev_pwm)
            
            if final_pwm > 0:
                turn_on(pwm, final_pwm)
            else:
                turn_off(pwm)

            prev_pwm = final_pwm

            trim_log_file()
            logger.info(f"Sleep {_SleepTime}sec")
            time.sleep(_SleepTime)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Exiting loop...")
            break
        except Exception as e:
            logger.error("Unhandled exception in main loop:")
            logger.error(traceback.format_exc())
            break

# Initialize logger globally
logger = setup_logger()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Unhandled exception in top-level code:")
        logger.error(traceback.format_exc())
    finally:
        release_resources()
