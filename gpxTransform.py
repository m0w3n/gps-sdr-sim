from optparse import OptionParser
from xml.dom import minidom
from datetime import datetime
from decimal import Decimal

# https://github.com/osqzss/gps-sdr-sim/issues/301

def rstripZero(dataList):
    result = []
    for data in dataList:
        data = data.rstrip("0")
        if len(data) > 0:
            if data[-1] == ".":
                data += "0"
            result.append(data)
        else:
            result.append("0.0")

    return result

def coordItemToFile(coordItem, output_file):
    csv_data = []  # [time, lat, lon, ele]
    for itemIndex in range(0,len(coordItem) - 1,1):
        p1 = coordItem[itemIndex]
        p2 = coordItem[itemIndex + 1]
        t = (p2["time"] - p1["time"]) * 5  # 0.2s采样
        # print(itemIndex, p1, p2, t)

        lat = (p2["lat"] - p1["lat"])/t
        lon = (p2["lon"] - p1["lon"])/t
        alt = (p2["alt"] - p1["alt"])/t

        csv_data.append([format(p1["time"], '.1f'), str(p1["lat"]), str(p1["lon"]), str(p1["alt"])])

        if int(t) > 1:
            for i in range(1, int(t), 1):
                time_t = format((p1["time"] + Decimal(i/5)), '.1f')
                lat_t = format(p1["lat"] + i * lat, '.9f')
                lon_t = format(p1["lon"] + i * lon, '.9f')
                alt_t = format(p1["alt"] + i * alt, '.3f')
                csv_data.append([str(time_t), str(lat_t).rstrip("0"), str(lon_t).rstrip("0"), str(alt_t).rstrip("0")])

        if itemIndex == len(coordItem) - 2:
            csv_data.append([format(p2["time"], '.1f'), str(p2["lat"]), str(p2["lon"]), str(p2["alt"])])

    with open(output_file, 'w', encoding='utf-8') as file:
        # 写入
        for csv_item in csv_data:
            data = ",".join(rstripZero(csv_item)) + "\n"
            file.write(data)
    file.close()

# 解析两步路导出的KML格式（轨迹）文件
def parseKML2CSV(input_file, output_file):
    # 解析XML文件
    doc = minidom.parse(input_file)
    root = doc.documentElement

    # 遍历XML元素
    items = root.getElementsByTagName('gx:coord')
    coordItem = []
    for item in items:
        itemValue = item.firstChild.nodeValue.split(" ")
        # print(item.firstChild.nodeValue, itemValue)
        lat = itemValue[1]
        lon = itemValue[0]
        alt = itemValue[2]
        coordItem.append({"lat": Decimal(lat), "lon": Decimal(lon), "alt": Decimal(alt)})

    items = root.getElementsByTagName('when')
    if len(items) != len(coordItem):
        print("格式错误!")
        return
    time_spend = Decimal('0.0')
    time_start = None
    itemIndex = 0
    for item in items:
        itemValue = item.firstChild.nodeValue
        if itemIndex == 0:
            time_start = datetime.strptime(itemValue, "%Y-%m-%dT%H:%M:%SZ")
        time_end = datetime.strptime(itemValue, "%Y-%m-%dT%H:%M:%SZ")
        time_spend = time_end.timestamp() - time_start.timestamp()
        coordItem[itemIndex]["time"] = Decimal(time_spend)
        # print(itemIndex, coordItem[itemIndex])
        itemIndex += 1

    coordItemToFile(coordItem, output_file)

# 解析两步路导出的GPX格式文件
def parseGPX2CSV(input_file, output_file):
    # 解析XML文件
    doc = minidom.parse(input_file)
    root = doc.documentElement

    # 遍历XML元素
    items = root.getElementsByTagName('trkpt')  # 例如，查找所有<item>标签
    time_spend = Decimal('0.0')
    time_start = None
    itemIndex = 0
    coordItem = []
    for item in items:
        # print(item.getAttribute("lat"),item.getAttribute("lon"))
        ele_et = item.getElementsByTagName("ele")[0]
        time_et = item.getElementsByTagName("time")[0]
        if time_start is None:
            time_start = datetime.strptime(time_et.firstChild.nodeValue, "%Y-%m-%dT%H:%M:%SZ")
        time_end = datetime.strptime(time_et.firstChild.nodeValue, "%Y-%m-%dT%H:%M:%SZ")

        lat = Decimal(item.getAttribute("lat"))
        lon = Decimal(item.getAttribute("lon"))
        alt = Decimal(ele_et.firstChild.nodeValue)
        time_spend = time_end.timestamp() - time_start.timestamp()

        coordItem.append({"lat": Decimal(lat), "lon": Decimal(lon), "alt": Decimal(alt), "time": Decimal(time_spend)})
        # print(itemIndex, coordItem[itemIndex])
        itemIndex += 1

    coordItemToFile(coordItem, output_file)


def get_options():
    usage = "usage: python gpxTransform.py [options]"
    parser = OptionParser(usage)
    parser.add_option('-f','--input_file', default="", help='需要解析的gpx文件')
    parser.add_option('-o','--output_file', default="gpx.csv", help='输出的csv文件，默认: gpx.csv')
    options, args = parser.parse_args()

    input_file_suffix = options.input_file.split(".")[-1]
    if len(args) != 0 or input_file_suffix not in ("gpx", "kml"):
        parser.print_help()
        raise SystemExit(1)

    return (options)

if __name__ == '__main__':
    (options) = get_options()
    input_file = options.input_file
    output_file = options.output_file
    # options = {'input_file': '.\\上班.kml', 'output_file': '上班.csv'}
    # options = {'input_file': '.\\泰山.gpx', 'output_file': '泰山.csv'}
    # input_file = options["input_file"]
    # output_file = options["output_file"]
    input_file_suffix = input_file.split(".")[-1]
    if input_file_suffix == "gpx":
        parseGPX2CSV(input_file, output_file)
    elif input_file_suffix == "kml":
        parseKML2CSV(input_file, output_file)


