## pi_lcd_dashboard

A tft_lcd dashboard for raspberry pi.

Based on [WaveShare_1.3Inch_LCD_HAT](https://m.tb.cn/h.45fWt0A?sm=2515b6) ←Click to buy from taobao.com

### Overview

- CPU status
<img src="https://blog-pics-1257119641.cos.ap-beijing.myqcloud.com/CPU.jpg" height="300px" />
- Memory status
<img src="https://blog-pics-1257119641.cos.ap-beijing.myqcloud.com/MEM.jpg" height="300px" />
- Host status
<img src="https://blog-pics-1257119641.cos.ap-beijing.myqcloud.com/STAT.jpg" height="300px" />
- Network status
<img src="https://blog-pics-1257119641.cos.ap-beijing.myqcloud.com/NET.jpg" height="300px" />

### Fast start

1. Clone this rep and run `sudo python2.7 mytft.py`
2. Wait several seconds until the screan flash a white pic.
3. Press `KEY1` to open the screan.
4. Press down `rocker_key` to Enable real time refresh, or the screan only refresh when you switch in pages.
5. Press down `KEY2` to Enable the network speed monitor.
6. Toggle the `rocker_key` to change current page

### Dependency

`Python 2.7` `RPi.GPIO` `psutil` `PIL` `spidev` `numpy`

### Thanks

Thanks for nxez/pi-dashboard project's good UI design
Thanks for WaveShare's hardware driver and demo.