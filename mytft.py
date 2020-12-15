# coding: utf-8
import spidev as SPI
import ST7789
import time
import subprocess
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from threading import _Timer
import os  
import socket, fcntl, struct  
import psutil

cpu_info = ""
net_id = "wlan0"
with open('/proc/cpuinfo','r') as f:
  cpu_info = f.read()
cpu_info.replace(" ", "")
cpu_info.replace("\t", "")
process_model = ""
BogoMIPS = ""
model_str_index = -1
for line in cpu_info.split('\n'):
    model_str_index = line.find("model name\t: ")
    if model_str_index != -1:
        # print(line)
        process_model = line[line.find(":")+1:len(line)]
    model_str_index = line.find("BogoMIPS\t: ")
    if model_str_index != -1:
        # print(line)
        BogoMIPS = line[line.find(":")+1:len(line)]

def get_ip2(ifname):  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

class RepeatingTimer(_Timer): 
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
#GPIO define
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24

KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13

KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16

KEY_LIST  =  (21 ,20, 16)

RST = 27
DC = 25
BL = 24
bus = 0 
device = 0 

# 240x240 display with hardware SPI:
disp = ST7789.ST7789(SPI.SpiDev(bus, device),RST, DC, BL)
disp.Init()

# Clear display.
disp.clear()
disp.sleep()

#init GPIO
# for P4:
# sudo vi /boot/config.txt
# gpio=6,19,5,26,13,21,20,16=pu
GPIO.setmode(GPIO.BCM) 
GPIO.setup(KEY_UP_PIN,      GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_DOWN_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_LEFT_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_LIST,        GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up

imgs = []
imgs.append(Image.open('/home/pi/Downloads/pi-tft/python/CPU.png').convert("RGBA"))
imgs.append(Image.open('/home/pi/Downloads/pi-tft/python/MEM.png').convert("RGBA"))
imgs.append(Image.open('/home/pi/Downloads/pi-tft/python/STAT.png').convert("RGBA"))
imgs.append(Image.open('/home/pi/Downloads/pi-tft/python/NET.png').convert("RGBA"))



current_page = 0
is_active = 0

def show_center_str(draw, str, ypos, font,center):
    width, height= font.getsize(str)
    x = center - width/2
    draw.text((x, ypos), str, font = font) #Show ip addr


def swicth_page_right(channel):
    global current_page
    global is_active
    if is_active == 1:
        current_page = (current_page+1)%4
        show_ip()
        
GPIO.add_event_detect(KEY_RIGHT_PIN, GPIO.RISING, callback=swicth_page_right,bouncetime=200)

def swicth_page_left(channel):
    global current_page
    global is_active
    if is_active == 1:
        current_page = (current_page+3)%4
        show_ip()
        
GPIO.add_event_detect(KEY_LEFT_PIN, GPIO.RISING, callback=swicth_page_left,bouncetime=200)

max_net_graphics_time = 16
speed_recv_list = [0 for i in range(max_net_graphics_time)]
speed_sent_list = [0 for i in range(max_net_graphics_time)]
last_net_recv = 0
last_net_sent = 0
current_net_buffer_index = 0

def calc_net_speed():
    global current_net_buffer_index
    global last_net_recv
    global last_net_sent
    global speed_recv_list
    global speed_sent_list
    global max_net_graphics_time
    net_io = psutil.net_io_counters(pernic=True)[net_id]
    net_recv = net_io.bytes_recv
    net_sent = net_io.bytes_sent
    speed_recv_list[current_net_buffer_index] = net_recv - last_net_recv
    speed_sent_list[current_net_buffer_index] = net_sent - last_net_sent
    last_net_recv = net_recv
    last_net_sent = net_sent
    current_net_buffer_index = (current_net_buffer_index+1) % max_net_graphics_time
    return

net_calc_timer = RepeatingTimer(1, calc_net_speed)


def draw_content_net(img):
    global current_net_buffer_index
    global last_net_recv
    global last_net_sent
    global speed_recv_list
    global speed_sent_list
    global max_net_graphics_time
    memory_convent = 1000
    y_max = 1
    y_multi = 1
    x_max = 10
    unit = "KB"
    last_speed_index = (current_net_buffer_index+max_net_graphics_time-1)%max_net_graphics_time
    #print(speed_sent_list[last_speed_index])
    max_val = 1.0*max(speed_sent_list + speed_recv_list)
    #print(speed_sent_list + speed_recv_list)
    #print(max_val)
    #if max_val/memory_convent > y_max:
    #    if max_val/memory_convent
    while max_val/memory_convent > y_max:
        if y_max == 1:
            y_max = 2
        elif y_max == 2:
            y_max = 5
        elif y_max == 5:
            y_max = 1
            memory_convent *= 10
    if memory_convent >= 1000*1000*1000:
        unit = "G"
        y_multi = memory_convent /1000*1000*1000
    elif memory_convent >= 1000*1000:
        unit = "M"
        y_multi = memory_convent /1000*1000
    elif memory_convent >= 1000:
        unit = "K"
        y_multi = memory_convent /1000
    else :
        unit = "B"
        y_multi = memory_convent
    #print(str(y_max*y_multi)+unit)
    speed_recv = 1.0*y_multi*speed_recv_list[last_speed_index]/memory_convent
    speed_sent = 1.0*y_multi*speed_sent_list[last_speed_index]/memory_convent
    tmp = Image.new('RGBA', img.size, (0,0,0,0)) # add background
    draw = ImageDraw.Draw(tmp)
    draw.rectangle(((30, 60), (210, 75)), fill=(255,255,153,127))# MEM 
    draw.rectangle(((30, 80), (210, 200)), fill=(204,204,255,127))# MEM 
    #draw.line([(30,80),(210,80),(210,200),(30,200),(30,80)], fill =(85,191,59), width = 2)
    last_x = 30
    last_y = 200 - 120.0*speed_recv_list[current_net_buffer_index]/memory_convent/y_max
    

    for i in range(max_net_graphics_time):
        current_index = (current_net_buffer_index+i)%max_net_graphics_time
        current_x = 30 + 12*i
        current_y = 200 - 120.0*(1.0*speed_recv_list[current_index]/memory_convent)/y_max
        draw.line([(last_x, last_y), (current_x, current_y)],fill =(85,191,59),width = 2)
        last_x = current_x
        last_y = current_y
    last_x = 30
    last_y = 200 - 120.0*speed_sent_list[current_net_buffer_index]/memory_convent/y_max
    for i in range(max_net_graphics_time):
        current_index = (current_net_buffer_index+i)%max_net_graphics_time
        current_x = 30 + 12*i
        current_y = 200 - 120.0*(1.0*speed_sent_list[current_index]/memory_convent)/y_max
        draw.line([(last_x, last_y), (current_x, current_y)],fill =(23,138,235),width = 2)
        last_x = current_x
        last_y = current_y

    img = Image.alpha_composite(img, tmp)
    draw = ImageDraw.Draw(img)
    Font1 = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf",14)
    draw.ink = 0 + 0 * 256 + 0 * 256 * 256
    
    show_center_str(draw,net_id, 60, Font1,120) #Show MEM
    show_center_str(draw,"T:"+"{:6.1f}".format(speed_sent)+unit+"/s", 200, Font1,75) #Show MEM
    show_center_str(draw,"R:"+"{:6.1f}".format(speed_recv)+unit+"/s", 200, Font1,165) #Show MEM
    show_center_str(draw,"T:"+"{:7.1f}".format(last_net_sent/(1000*1000)) + "MB", 215, Font1,75) #Show MEM
    show_center_str(draw,"R:"+"{:7.1f}".format(last_net_recv/(1000*1000)) + "MB", 215, Font1,165) #Show MEM

    show_center_str(draw,"0", 193, Font1,15) #Show y_index
    show_center_str(draw,str(y_max*y_multi)+unit, 68, Font1,15) #Show y_index
    return img

def draw_content_stat(img):
    icon = Image.open('/home/pi/Downloads/pi-tft/python/iconspi-40.png')	#Image.new("RGB", (disp.width, disp.height), "WHITE") 100,42
    icon = icon.convert("RGBA")
    r, g, b, a = icon.split()
    img.paste(icon, (100,42),mask=a)#Show pi icon

    tmp = Image.new('RGBA', img.size, (0,0,0,0)) # add background
    draw = ImageDraw.Draw(tmp)
    draw.rectangle(((36, 87), (204, 120)), fill=(255,255,153,127))
    draw.rectangle(((36, 125), (204, 180)), fill=(204,204,255,127))
    draw.rectangle(((36, 185), (204, 230)), fill=(255,255,153,127))

    img = Image.alpha_composite(img, tmp)



    draw = ImageDraw.Draw(img)
    Font1 = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf",14)
    draw.ink = 0 + 0 * 256 + 0 * 256 * 256
    show_center_str(draw,"IP:" + get_ip2("wlan0"), 95, Font1, 120)
    show_center_str(draw, "TIME", 125, Font1,120)
    show_center_str(draw,  time.strftime('%H:%M:%S',time.localtime(time.time())), 143, Font1,120)
    show_center_str(draw,  time.strftime('%Y-%m-%d',time.localtime(time.time())), 161, Font1,120)
    show_center_str(draw,   "HOSTNAME", 191, Font1,120)
    show_center_str(draw,   socket.gethostname(), 209, Font1,120)
    return img

def draw_content_mem(img):
    memory_convent = 1024 * 1024
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_usage = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters(perdisk=False)
    avr1, avr5, avr10 = psutil.getloadavg()

    tmp = Image.new('RGBA', img.size, (0,0,0,0)) # add background
    draw = ImageDraw.Draw(tmp)
    mem_percent = 100.0*mem.used/mem.total
    percent_degree = 180 * (mem_percent/100.0)
    draw.arc((60,60-10,180,180-10), 180, 0, fill = (85,191,59))
    draw.arc((80,80-10,160,160-10), 180, 0, fill = (85,191,59))
    draw.pieslice((60,60-10,180,180-10), 180, 180+percent_degree, fill = (85,191,59))
    draw.pieslice((80+1,80-10+1,160-1,160-10-1), 180, 0, fill = (235,235,235))
    draw.line((160,120-10,180,120-10),fill = (85,191,59))

    draw.rectangle(((24, 127), (216, 226)), fill=(205,253,159,127))

    draw.rectangle(((24, 127), (216, 226)), fill=(205,253,159,127))# MEM 
    draw.rectangle(((24, 140), (72, 168)), fill=(255,254,205,127)) # MEM USED
    draw.rectangle(((72, 140), (120, 168)), fill=(224,224,224,127)) # MEM CACHED
    draw.rectangle(((120, 140), (168, 168)), fill=(253,204,203,127)) # MEM FREE
    draw.rectangle(((168, 140), (216, 168)), fill=(155,206,253,127)) # MEM SWAP
    draw.rectangle(((24, 168), (88, 196)), fill=(241,169,160,127)) # AvrLoad 1min
    draw.rectangle(((88, 168), (152, 196)), fill=(255,192,192,127)) # AvrLoad 5min
    draw.rectangle(((152, 168), (216, 196)), fill=(241,169,160,127)) # AvrLoad 10min
    draw.rectangle(((24, 140+56), (72, 170+56)), fill=(255,254,205,127)) # DISK USED
    draw.rectangle(((72, 140+56), (120, 170+56)), fill=(224,224,224,127)) # DISK TOTAL
    draw.rectangle(((120, 140+56), (168, 170+56)), fill=(253,204,203,127)) # DISK READ
    draw.rectangle(((168, 140+56), (216, 170+56)), fill=(155,206,253,127)) # DISK WRITE

    img = Image.alpha_composite(img, tmp)
    draw = ImageDraw.Draw(img)
    Font1 = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf",12)
    draw.ink = 0 + 0 * 256 + 0 * 256 * 256
    
    show_center_str(draw,"0", 110, Font1,70) #Show MEM
    show_center_str(draw,str( mem.total/( memory_convent )), 110, Font1,170) #Show MEM

    
    show_center_str(draw,"MEM", 127, Font1,120) #Show MEM
    show_center_str(draw,"{:.1f}".format(100.0*mem.used/mem.total)+"%", 144, Font1,48) #Show MEM USED
    show_center_str(draw,"USED", 155, Font1,48) #Show MEM USED
    show_center_str(draw,"{:.1f}".format(mem.cached/( memory_convent ))+"MB", 144, Font1,96) #Show MEM CACHED
    show_center_str(draw,"CACHED", 155, Font1,96) #Show MEM CACHED
    show_center_str(draw, "{:.1f}".format(mem.free/( memory_convent ))+"MB", 144, Font1,144) #Show MEM FREE
    show_center_str(draw,"FREE", 155, Font1,144) #Show MEM FREE
    show_center_str(draw, "{:.1f}".format(swap.total/( memory_convent )) + "MB", 144, Font1,192) #Show MEM SWAP
    show_center_str(draw,"SWAP", 155, Font1,192) #Show MEM SWAP

    
    show_center_str(draw,str(avr1), 172, Font1,56) #Show AvrLoad 1
    show_center_str(draw,"AVR1M", 183, Font1,56) #Show AvrLoad 1
    show_center_str(draw,str(avr5), 172, Font1,120) #Show AvrLoad 5
    show_center_str(draw,"AVR5M", 183, Font1,120) #Show AvrLoad 5
    show_center_str(draw,str(avr10), 172, Font1,184) #Show AvrLoad 10
    show_center_str(draw,"AVR10M", 183, Font1,184) #Show AvrLoad 10

    show_center_str(draw,"{:.1f}".format(disk_usage.used/( memory_convent *1024))+"GB", 144+56, Font1,48) #Show DISK USED
    show_center_str(draw,"DISK", 155+56, Font1,48) #Show DISK USED
    show_center_str(draw,"{:.1f}".format(disk_usage.total/( memory_convent*1024 ))+"GB", 144+56, Font1,96) #Show DISK TOTAL
    show_center_str(draw,"TOTAL", 155+56, Font1,96) #Show DISK TOTAL
    show_center_str(draw, "{:.1f}".format(disk_usage.free/( memory_convent*1024 ))+"GB", 144+56, Font1,144) #Show DISK READ
    show_center_str(draw,"FREE", 155+56, Font1,144) #Show DISK READ
    show_center_str(draw, "{:.1f}".format(100.0* disk_io.busy_time/( 1000*1000 )) + "%", 144+56, Font1,192) #Show DISK WRITE
    show_center_str(draw,"I/O", 155+56, Font1,192) #Show DISK WRITE



    show_center_str(draw,str( mem.used/( memory_convent ) ) + "MB", 95, Font1,120) # Show MEM percent
    return img

def draw_content_cpu(img):
    cpu_status = psutil.cpu_times()
    cpu_percent = psutil.cpu_percent()
    tmp = Image.new('RGBA', img.size, (0,0,0,0)) # add background
    draw = ImageDraw.Draw(tmp)
    percent_degree = 180 * (cpu_percent/100.0)
    draw.arc((60,60-10,180,180-10), 180, 0, fill = (85,191,59))
    draw.arc((80,80-10,160,160-10), 180, 0, fill = (85,191,59))
    draw.pieslice((60,60-10,180,180-10), 180, 180+percent_degree, fill = (85,191,59))
    draw.pieslice((80+1,80-10+1,160-1,160-10-1), 180, 0, fill = (235,235,235))
    draw.line((160,120-10,180,120-10),fill = (85,191,59))

    draw.rectangle(((24, 127), (216, 226)), fill=(205,253,159,127))
    draw.rectangle(((24, 140), (72, 168)), fill=(255,254,205,127)) # cpu freq
    draw.rectangle(((72, 140), (120, 168)), fill=(224,224,224,127)) # cpu count
    draw.rectangle(((120, 140), (168, 168)), fill=(253,204,203,127)) # cpu temp
    draw.rectangle(((168, 140), (216, 168)), fill=(155,206,253,127)) # cpu IDLE

    draw.rectangle(((24, 168), (56, 196)), fill=(241,169,160,127)) # cpu USER
    draw.rectangle(((56, 168), (88, 196)), fill=(255,192,192,127)) # cpu SYS
    draw.rectangle(((88, 168), (120, 196)), fill=(241,169,160,127)) # cpu NICE
    draw.rectangle(((120, 168), (152, 196)), fill=(255,192,192,127)) # cpu IOW
    draw.rectangle(((152, 168), (184, 196)), fill=(241,169,160,127)) # cpu IRQ
    draw.rectangle(((184, 168), (216, 196)), fill=(255,192,192,127)) # cpu SIRQ
    
    draw.rectangle(((24, 196), (216, 226)), fill=(224,224,224,255)) # cpu HARDWARE

    img = Image.alpha_composite(img, tmp)
    draw = ImageDraw.Draw(img)
    Font1 = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf",12)
    draw.ink = 0 + 0 * 256 + 0 * 256 * 256

    show_center_str(draw,"0", 110, Font1,70) #Show CPU
    show_center_str(draw,"100", 110, Font1,170) #Show CPU
    show_center_str(draw,str (cpu_percent) + "%", 95, Font1,120)

    show_center_str(draw,"CPU", 127, Font1,120) #Show CPU
    show_center_str(draw,str(int(psutil.cpu_freq().current)), 144, Font1,48) #Show CPU freq
    show_center_str(draw,"MHz", 155, Font1,48) #Show CPU freq
    show_center_str(draw,str(psutil.cpu_count()), 144, Font1,96) #Show CPU count
    show_center_str(draw,"CORE", 155, Font1,96) #Show CPU count
    show_center_str(draw, "{:.2f}".format(psutil.sensors_temperatures()['cpu_thermal'][0].current), 144, Font1,144) #Show CPU temp
    show_center_str(draw,"°C", 155, Font1,144) #Show CPU temp
    show_center_str(draw, "{:.1f}".format(100.0-cpu_percent) + "%", 144, Font1,192) #Show CPU IDLE
    show_center_str(draw,"IDLE", 155, Font1,192) #Show CPU IDLE
    cpu_time_percent = psutil.cpu_times_percent()

    show_center_str(draw,str(cpu_time_percent.user), 172, Font1,40) #Show CPU USER
    show_center_str(draw,"USER", 183, Font1,40) #Show CPU USER
    show_center_str(draw,str(cpu_time_percent.system), 172, Font1,72) #Show CPU SYS
    show_center_str(draw,"SYS", 183, Font1,72) #Show CPU SYS
    show_center_str(draw,str(cpu_time_percent.nice), 172, Font1,104) #Show CPU NICE
    show_center_str(draw,"NICE", 183, Font1,104) #Show CPU NICE
    show_center_str(draw,str(cpu_time_percent.iowait), 172, Font1,136) #Show CPU IOW
    show_center_str(draw,"IOW", 183, Font1,136) #Show CPU IOW
    show_center_str(draw,str(cpu_time_percent.irq), 172, Font1,168) #Show CPU IRQ
    show_center_str(draw,"IRQ", 183, Font1,168) #Show CPU IRQ
    show_center_str(draw,str(cpu_time_percent.softirq), 172, Font1,200) #Show CPU SIRQ
    show_center_str(draw,"SIRQ", 183, Font1,200) #Show CPU SIRQ
    

    Font1 = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf",10)
    show_center_str(draw,process_model, 200, Font1,120) #Show CPU HARDWARE
    show_center_str(draw,"BogoMIPS:" + BogoMIPS, 213, Font1,120) #Show CPU HARDWARE

    return img


def show_ip():
    image1 = imgs[current_page]
    if current_page == 3:
        image1 = draw_content_net(image1)
    if current_page == 2:
        image1 = draw_content_stat(image1)
    if current_page == 1:
        image1 = draw_content_mem(image1)
    if current_page == 0:
        image1 = draw_content_cpu(image1)
    disp.ShowImage(image1,0,0)


display_timer = RepeatingTimer(1, show_ip)
def start_interval(channel):
    if is_active == 1:
        if display_timer.is_alive():
            display_timer.cancel()
        else:
            display_timer.start()
    

GPIO.add_event_detect(KEY_PRESS_PIN, GPIO.RISING, callback=start_interval,bouncetime=200)

def start_net_calc(channel):
    global last_net_recv
    global last_net_sent
    if is_active == 1:
        if net_calc_timer.is_alive():
            net_calc_timer.cancel()
        else:
            net_io = psutil.net_io_counters(pernic=True)[net_id]
            last_net_recv = net_io.bytes_recv
            last_net_sent = net_io.bytes_sent
            net_calc_timer.start()

GPIO.add_event_detect(KEY2_PIN, GPIO.RISING, callback=start_net_calc,bouncetime=200)


while 1:
    GPIO.wait_for_edge(KEY1_PIN, GPIO.RISING)
    is_active = 1
    disp.wakeup()
    show_ip()
    GPIO.wait_for_edge(KEY1_PIN, GPIO.RISING)
    disp.sleep()
    is_active = 0
#130 - 226