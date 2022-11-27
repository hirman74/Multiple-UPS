#!/usr/bin/python3
import os
import json
import time
from subprocess import Popen, PIPE
# subprocess.run(args, *, stdin=None, input=None, stdout=None, stderr=None, capture_output=False, shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None, text=None, env=None, universal_newlines=None, **other_popen_kwargs)

def secondsTime():
    getHourMinuteSeconds = time.strftime("%Y%b%d_%H%M%S")
    return getHourMinuteSeconds

def checkLogFileSize(filename):
    if os.path.getsize(filename) > 1000:
        return True

def collectingData(host):
    oidToCheck = ['upsBaseBatteryTimeOnBattery','upsSecondsOnBattery','upsSmartInputLineVoltage', 'upsInputVoltage1']
    for eachOIDName, thisDict in snmpMIBS.items(): #name:value pair
        if eachOIDName in oidToCheck:

            snmpCMD.append(host.strip())
            snmpCMD.append(thisDict['oidString'])

            querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
            stdout, stderr = querySNMP.communicate()

            snmpValue = stdout.split(':')[-1]
            snmpErrors = stderr.split(':')[-1]
            # print(snmpValue)
            # print(snmpErrors)
            snmpResults = updateResult(host, snmpValue, eachOIDName)
    return snmpResults

def updateResult(host, snmpValue, eachOIDName):
    snmpResults = {
        'hostIP' : None,
        'upsBaseBatteryTimeOnBattery': {
            'value' : None,
            'status' : None
        },
        'upsSmartInputLineVoltage' : {
            'value' : None,
            'status' : None
        },
        'upsSecondsOnBattery' : {
            'value' : None,
            'status' : None
        },
        'upsInputVoltage1' : {
            'value' : None,
            'status' : None
        },
        'upsInputVoltage2' : {
            'value' : None,
            'status' : None
        },
        'upsInputVoltage3' : {
            'value' : None,
            'status' : None
        }
    }
    snmpResults['hostIP'] = host
    if 'No response' in snmpValue:
        snmpResults[eachOIDName]['status'] = 'DOWN'
    if eval (snmpValue.strip() + snmpMIBS[eachOIDName]['expectValue']):
        snmpResults[eachOIDName]['status'] = 'GOOD'
        snmpResults[eachOIDName]['value'] = snmpValue.strip()
    else:
        snmpResults[eachOIDName]['status'] = 'BAD'
        snmpResults[eachOIDName]['value'] = snmpValue.strip()
    return snmpResults


def main(hostList):
    for host in hostList:
        print ('Collecting data from host: ' + host)
        snmpResults = collectingData(host)
        time.sleep(1)
        listResult.append(snmpResults)
    return listResult

def checkBattery(host, snmpGet):
    upsBatteryStatus = snmpGet + host + ' .1.3.6.1.2.1.33.1.2.1.0' 
    # INTEGER {unknown(1),batteryNormal(2),batteryLow(3),batteryDepleted(4)
    if upsBatteryStatus == 1:
        return 'Battery Status: Unknown'
    elif upsBatteryStatus == 2:
        return 'Battery Status: Normal'
    elif upsBatteryStatus == 3:
        return 'Battery Status: Low'
    elif upsBatteryStatus == 4:
        return 'Battery Status: Depleted'

def testFile(filenames):
    getAllResuls = [None] * len(filenames)
    for idx in range(len(filenames)):
        snmpResults = {
            'hostIP' : None,
            'upsBaseBatteryTimeOnBattery': {
                'value' : None,
                'status' : None
            },
            'upsSmartInputLineVoltage' : {
                'value' : None,
                'status' : None
            },
            'upsSecondsOnBattery' : {
                'value' : None,
                'status' : None
            },
            'upsInputVoltage1' : {
                'value' : None,
                'status' : None
            },
            'upsInputVoltage2' : {
                'value' : None,
                'status' : None
            },
            'upsInputVoltage3' : {
                'value' : None,
                'status' : None
            }
        }
        with open(filenames[idx], 'r') as fp:
            for line in fp:
                if line.strip():
                    splitValues = line.split(':')
                    snmpValue = splitValues[-1].strip()
                    viewOID = splitValues[0].split('=')[0].strip()

                    for eachName, thisDict in snmpMIBS.items():
                        if thisDict['oidString'] == viewOID:
                            eachOIDName = eachName

                    snmpResults['hostIP'] = filenames[idx]
                    if 'No response' in snmpValue:
                        snmpResults[eachOIDName]['status'] = 'DOWN'
                    if eval (snmpValue.strip() + snmpMIBS[eachOIDName]['expectValue']):
                        snmpResults[eachOIDName]['status'] = 'GOOD'
                        snmpResults[eachOIDName]['value'] = snmpValue.strip()
                    else:
                        snmpResults[eachOIDName]['status'] = 'BAD'
                        snmpResults[eachOIDName]['value'] = snmpValue.strip()
        getAllResuls[idx] = snmpResults
    return getAllResuls

if __name__ == '__main__':
    hostList = ('175.50.44.1', '176.50.44.1')
    snmpMIBS = {
        'upsBaseBatteryTimeOnBattery': {
            'mibName' : 'upsBaseBatteryTimeOnBattery',
            'oidString' : '.1.3.6.1.4.1.935.1.1.1.2.1.2.0',
            'expectValue' : ' < 60',
            'fromBranch' : 'PPC'
        },
        'upsSmartInputLineVoltage' : {
            'mibName' : 'upsSmartInputLineVoltage',
            'oidString' : '.1.3.6.1.4.1.935.1.1.1.3.2.1.0',
            'expectValue' : ' > 2000',
            'fromBranch' : 'PPC'
        },
        'upsSecondsOnBattery' : {
            'mibName' : 'upsSecondsOnBattery',
            'oidString' : '.1.3.6.1.2.1.33.1.2.2.0',
            'expectValue' : ' < 60',
            'fromBranch' : 'upsMIB'
        },
        'upsInputVoltage1' : {
            'mibName' : 'upsInputVoltage1',
            'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.1',
            'expectValue' : ' > 200',
            'fromBranch' : 'upsMIB'
        },
        'upsInputVoltage2' : {
            'mibName' : 'upsInputVoltage2',
            'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.2',
            'expectValue' : ' > 200',
            'fromBranch' : 'upsMIB'
        },
        'upsInputVoltage3' : {
            'mibName' : 'upsInputVoltage3',
            'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.3',
            'expectValue' : ' > 200',
            'fromBranch' : 'upsMIB'
        }
    }

    snmpFolder = '/usr/bin/'
    snmpCMD = [snmpFolder + 'snmpget']
    snmpARG = ['-v', '2c', '-c', 'public', '-OQ', '-t', '10', '-r', '2']
    for str in snmpARG:
        snmpCMD.append(str)

    listResult = [{'startTimeCollect': secondsTime()}]
    listResult = main(hostList)
    # getAllResuls = testFile(filenames = ('good_IP_175.50.44.1.txt', 'bad_IP_175.50.44.1.txt') )
    # with open('result.json', 'w') as f:
    #     f.writelines(json.dumps(getAllResuls, indent=4, separators=(", ", " : ")))

    resultedFile = 'statusUPS.json'
    if os.path.isfile(resultedFile):
        if checkLogFileSize(resultedFile):
            with open('statusUPS.json', 'w') as f:
                f.writelines(json.dumps(listResult, indent=4, separators=(", ", " : ")))
        else:
            with open('statusUPS.json', 'a') as f:
                f.writelines(json.dumps(listResult, indent=4, separators=(", ", " : ")))
