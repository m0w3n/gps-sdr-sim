# 项目说明

1. 修改默认3000的采样为30000，支持更长时间的GPS数据生成。

2. 对两步路导出的GPX和KML（轨迹）文件解析为csv，并按照 0.2s 的间隔自动补全数据。

    ```
    python3 gpxTransform.py -f 泰山.gpx -o 泰山_gpx.csv
    python3 gpxTransform.py -f 泰山.kml -o 泰山_kml.csv
    ```

# 环境搭建

ubuntu 22.04

```
sudo apt-get install git build-essential cmake libusb-1.0-0-dev liblog4cpp5-dev libboost-dev libboost-system-dev libboost-thread-dev libboost-program-options-dev swig pkg-config libfftw3-dev

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install gnuradio gnuradio-dev gr-iqbal gr-osmosdr
sudo apt-get install hackrf libhackrf-dev
sudo apt-get install gqrx-sdr

# sudo apt-get remove --auto-remove hackrf
```

# GPS-SDR-SIM 编译

本仓库是官方项目：https://github.com/osqzss/gps-sdr-sim 的克隆，增加了GPS动态欺骗的 ecjtu 操场绕圈坐标。

```
git clone https://github.com/m0w3n/gps-sdr-sim.git
cd gps-sdr-sim
gcc gpssim.c -lm -O3 -o gps-sdr-sim
```

编译完成后，你当前文件夹下就会出现可执行程序gps-sdr-sim。

# 星历下载

进入武大IGS中心：[武汉大学IGS数据中心 (gnsswhu.cn)](http://www.igs.gnsswhu.cn/index.php)，选择广播星历，选择一个日期区间就可以下载；天数越大越近。下载N文件：brdc0970.25n.gz，解压后 brdc0970.25n 。

- 097天
- 25年

# 生成动态或静态 HackRF IQ 样本

| 命令                                                         | 介绍                                                         |
| :----------------------------------------------------------- | :----------------------------------------------------------- |
| gps-sdr-sim -e brdc0970.25n -b 8 -u circle.csv               | User motion file in ECEF x, y, z format (dynamic mode)       |
| gps-sdr-sim -e brdc0970.25n  -b 8 -x circle_llh.csv          | User motion file in lat, lon, height format (dynamic mode)<br>纬度、经度、高度，动态GPS数据，表格的第一列是 0.1S<br>[使用我的动作文件时出错 ·问题 #301 ·OSQZSS/GPS-SDR-SIM 网关](https://github.com/osqzss/gps-sdr-sim/issues/301)，确保加速度平稳 |
| gps-sdr-sim -e brdc0970.25n  -b 8 -g triumphv3.txt           | NMEA GGA stream (dynamic mode)                               |
| gps-sdr-sim -e brdc0970.25n  -b 8 -l 30.286502,120.032669,100 | Lat,Lon,Hgt (static mode) e.g. 30.286502,120.032669,100<br>纬度、经度、高度，静态GPS数据 |

准备一个想要模拟的经纬度，如：115.870908,28.736908（华东交大理学院）

可以使用地图工具获得想要的坐标：[坐标拾取器 | 高德地图API](https://lbs.amap.com/tools/picker)

https://tool.lu/coordinate/、http://api.map.baidu.com/lbsapi/getpoint/index.html

轨迹生成网站：[NMEA Generator](https://nmeagen.org/)

输入命令（如果出现段错误，多试几次）：

```
# 静态欺骗，固定点
./gps-sdr-sim -e brdc0970.25n -l 28.736908,115.870908,100 -b 8 -o ./gpssim.bin
# 动态欺骗，绕圈点
./gps-sdr-sim -e brdc0970.25n -x circle_ecjtu.csv -b 8 -o ./gpssim_circle_ecjtu.bin
# 两步路轨迹模拟
./gps-sdr-sim -e brdc0970.25n -x 泰山_kml.csv -b 8 -o ./gpssim_泰山_kml.bin
```

- -e：指定RINEX格式GPS导航电文文件
- -l：指定经纬度和海拔（静态模式）
- -x：lat、lon、height格式的用户运动文件（动态模式）
- -b：指定采样精度（hackrf为8，blader为16）（不需要改）
- -o：生成bin文件的位置，这里要在路径的后边加上文件名

等待执行上述命令，执行结束后，你会发现你的文件夹中多了一个gpssim.bin文件，这个文件保存的就是我们模拟生成的GPS数据。

# 发送gps数据

```
hackrf_transfer -t gpssim.bin -f 1575420000 -s 2600000 -a 1 -x 0 -R
```

指定GPS数据，指定频率为1575420000 即民用GPS L1波段频率，指定采样速率2.6Msps，开启天线增益，指定TX VGA(IF)为0(为了限制影响范围，最大为47慎用！！！)，最后开启重复发射数据功能。

现在GPS信号就正常发送了。
