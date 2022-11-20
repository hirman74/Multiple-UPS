
def main(hostList):
    for host in hostList:
        print ('Collecting data from host: {0}'.format('host'))
        upsBaseBatteryTimeOnBattery, upsSmartInputLineVoltage = upsPPC(host)
        upsSecondsOnBattery, upsInputVoltage = upsMIB(host)
        if (upsBaseBatteryTimeOnBattery > 60 or upsSecondsOnBattery > 60) and (upsSmartInputLineVoltage < 200 or upsInputVoltage < 200):
            print ('{0} is running from Battery'.format('host'))

def upsPPC(host):
    upsBaseBatteryTimeOnBattery = 'snmpget -v 2c -c public -t 10 -r 2 ' + host + ' .1.3.6.1.4.1.935.1.1.1.2.1.2'
    upsSmartInputLineVoltage = 'snmpget -v 2c -c public -t 10 -r 2 ' + host + ' .1.3.6.1.4.1.935.1.1.1.3.2.1'
    return upsBaseBatteryTimeOnBattery, upsSmartInputLineVoltage

def upsMIB(host):
    upsSecondsOnBattery = 'snmpget -v 2c -c public -t 10 -r 2 ' + host + ' .1.3.6.1.2.1.33.1.2.2'    
    upsInputVoltage = 'snmpget -v 2c -c public -t 10 -r 2 ' + host + ' .1.3.6.1.2.1.33.1.3.3.1.3'
    return upsSecondsOnBattery, upsInputVoltage

def checkBattery(host):
    upsBatteryStatus = 'snmpget -v 2c -c public -t 10 -r 2 ' + host + ' .1.3.6.1.2.1.33.1.2.1' # INTEGER {unknown(1),batteryNormal(2),batteryLow(3),batteryDepleted(4)
    if upsBatteryStatus == 1:
        return 'Battery Status: Unknown'
    elif upsBatteryStatus == 2:
        return 'Battery Status: Normal'
    elif upsBatteryStatus == 3:
        return 'Battery Status: Low'
    elif upsBatteryStatus == 4:
        return 'Battery Status: Depleted'

if __name__ == '__main__':
    hostList = ('localhost', '192.168.10.12')
    main(hostList)
