#!/usr/bin/env python
"""
Command Handler for Ground Station Core
Handles pre/post pass actions, antenna selection, and email notifications
Cross-platform compatible (Windows/Linux)
"""

import os
import sys
import time
import glob
import serial
import smtplib
import subprocess
import platform
from datetime import date
from email import encoders
from os.path import basename
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

# Try to load config module
try:
    from config import get_config
    config = get_config()
    RESULTS_PREFIX = config.results_prefix
except ImportError:
    RESULTS_PREFIX = 'results'

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Serial port configuration - adjust for your hardware
ANT_SELECT_SERIAL_DEV = os.getenv('ANT_SERIAL_PORT', 'COM3' if IS_WINDOWS else '/dev/ttyUSB1')
ANT_SELECT_SERIAL_BAUD = 9600
ANT_SELECT_SERIAL_PARITY = serial.PARITY_NONE
ANT_SELECT_SERIAL_STOPBITS = serial.STOPBITS_ONE
ANT_SELECT_SERIAL_BYTESIZE = serial.EIGHTBITS

# Email configuration
EMAIL_NOTIFICATION_RECEPIENT = os.getenv('EMAIL_RECIPIENT', 'stanislav.barantsev@community.isunet.edu')
EMAIL_NOTIFICATION_CONFIG_FILE = os.getenv('EMAIL_CONFIG', 
    str(Path.home() / '.gsc' / 'email.cfg') if IS_WINDOWS else '/etc/gsc/email.cfg')


def send_email_notification(auth_file, attachments=[]):
    """
    Send email notification with attachments
    
    Args:
        auth_file: Path to authentication config file (contains login and password)
        attachments: List of file paths to attach
    
    Returns:
        bool: True if successful, False otherwise
    """
    client_login = ''
    client_password = ''

    try:
        auth_path = Path(auth_file)
        if not auth_path.exists():
            print(f'[email] couldn\'t open the file: {auth_file}')
            return False
            
        with open(auth_file, 'r') as reader:
            config_lines = reader.read().splitlines()
            
        if len(config_lines) < 2:
            print('[email] config file must contain at least 2 lines (login and password)')
            return False
            
        client_login = config_lines[0].strip()
        client_password = config_lines[1].strip()
        
    except Exception as e:
        print(f'[email] couldn\'t open the file: {e}')
        return False

    if client_login == '' or client_password == '': 
        print('[email] no client login or password specified')
        return False

    subject = "Satellite Pass Results from Ground Station Core"
    recepient = EMAIL_NOTIFICATION_RECEPIENT

    msg = MIMEMultipart()
    msg["To"] = recepient
    msg["From"] = client_login
    msg["Subject"] = subject

    body = "Hi there, please find the results for the latest satellite pass!"
    msg.attach(MIMEText(body, "plain"))

    for f in attachments or []:
        try:
            if not Path(f).exists():
                print(f'[email] attachment not found: {f}')
                continue
                
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(f)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)
        except Exception as e:
            print(f'[email] error attaching file {f}: {e}')

    text = msg.as_string()
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        ret = server.login(client_login, client_password)
        print('[email] authenticated successfully')
    except Exception as e:
        print(f'[email] wrong credentials, couldn\'t authenticate: {e}')
        return False

    try:
        server.sendmail(client_login, recepient, text)
        print('[email] email sent successfully')
    except Exception as e:
        print(f'[email] couldn\'t send the email: {e}')
        server.quit()
        return False

    server.quit()
    return True


def action_ant_select(args):
    """
    Select antenna based on frequency
    
    Args:
        args: List containing frequency in Hz
        
    Returns:
        bool: True if successful, False otherwise
    """
    if len(args) > 1 or len(args) < 1:
        print('Only one argument is needed (antenna number)')
        return False

    freq = float(args[0])
    print(f'Selecting antenna for frequency: {freq} Hz')

    if freq > 30e6 and freq < 300e6:
        # VHF input
        ant_num = '3'
    elif freq > 300e6 and freq < 3000e6:
        # UHF input
        ant_num = '1'
    else:
        # S-band input: not supported by default
        ant_num = '2'

    try:
        # Check if serial port exists
        if not Path(ANT_SELECT_SERIAL_DEV).exists() if not IS_WINDOWS else True:
            print(f'[antenna] Serial port {ANT_SELECT_SERIAL_DEV} not found')
            print('[antenna] Running in simulation mode')
            return True
            
        ser = serial.Serial(
            port=ANT_SELECT_SERIAL_DEV,
            baudrate=ANT_SELECT_SERIAL_BAUD,
            parity=ANT_SELECT_SERIAL_PARITY,
            stopbits=ANT_SELECT_SERIAL_STOPBITS,
            bytesize=ANT_SELECT_SERIAL_BYTESIZE,
            timeout=1
        )

        if not ser.isOpen():
            print('[antenna] Failed to open serial port')
            return False

        out = ''
        ser.write(ant_num.encode('utf-8'))
        time.sleep(0.1)
        
        while ser.inWaiting() > 0:
            out += ser.read(1).decode('utf-8')

        out = out.strip()
        if out == '':
            print('[antenna] No response from antenna controller')
            ser.close()
            return False

        print(f'[antenna] Response: {out}')
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f'[antenna] Serial error: {e}')
        print('[antenna] Running in simulation mode')
        return True
    except Exception as e:
        print(f'[antenna] Error: {e}')
        return False


def mkdir_cross_platform(path):
    """Create directory cross-platform"""
    Path(path).mkdir(parents=True, exist_ok=True)


def mv_cross_platform(pattern, dest):
    """Move files cross-platform"""
    files = glob.glob(pattern)
    for f in files:
        try:
            dest_path = Path(dest) / Path(f).name
            Path(f).rename(dest_path)
            print(f'Moved: {f} -> {dest_path}')
        except Exception as e:
            print(f'Error moving {f}: {e}')


# create directories, clean up old files
def action_pre_doit(args):
    """
    Pre-pass actions: create directories, select antenna
    
    Args:
        args: Command arguments (frequency for antenna selection)
    """
    print('== pre doit ==')
    today = date.today()
    results_dir = Path(RESULTS_PREFIX) / str(today)
    
    # Create results directory
    mkdir_cross_platform(str(results_dir))
    print(f'Created directory: {results_dir}')
    
    # Select antenna
    if args:
        action_ant_select(args)
    
    return True


# put files on storage, send notifications
def action_post_doit(args):
    """
    Post-pass actions: organize files, send email notifications
    
    Args:
        args: Command arguments (not used currently)
    """
    print('== post doit ==')
    today = date.today()
    results_dir = Path(RESULTS_PREFIX) / str(today)
    
    # Ensure results directory exists
    mkdir_cross_platform(str(results_dir))
    
    # Find result files
    files = glob.glob('*GMT.dat')
    
    if files:
        print(f'Found {len(files)} result files')
        
        # Send email notification if configured
        if Path(EMAIL_NOTIFICATION_CONFIG_FILE).exists():
            print('Sending email notification...')
            send_email_notification(EMAIL_NOTIFICATION_CONFIG_FILE, files)
        else:
            print(f'Email config not found: {EMAIL_NOTIFICATION_CONFIG_FILE}')
    else:
        print('No result files found')
    
    # Move result files
    print('Moving result files...')
    mv_cross_platform('*GMT.dat', str(results_dir))
    mv_cross_platform('*GMT.raw', str(results_dir))
    
    print('== post doit complete ==')
    return True

actions = {
            'pre_doit'   : action_pre_doit,
            'post_doit'  : action_post_doit,
            'ant_select' : action_ant_select,
          }

args = sys.argv
if len(args) < 2:
    print('No action specified')
    exit(1)

action = args[1]
func = actions.get(action)

if func == None:
    print('No action \'' + action + '\' found in list')
    print('Valid actions:')
    for key in actions.keys():
        print(' -> ' + key)
    exit(1)

args = args[2:]
func(args)
