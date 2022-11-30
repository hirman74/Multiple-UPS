#!/usr/bin/python3
import os
import json
import time
from subprocess import Popen, PIPE, check_output
# subprocess.run(args, *, stdin=None, input=None, stdout=None, stderr=None, capture_output=False, shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None, text=None, env=None, universal_newlines=None, **other_popen_kwargs)

def secondsTime():
    getHourMinuteSeconds = time.strftime("%Y%b%d_%H%M%S")
    return getHourMinuteSeconds

def checkLogFileSize(resultedFile):
    if os.path.getsize(resultedFile) > 1000:
        return True

def checkBattery(host, snmpResults):
    # upsBatteryStatus == .1.3.6.1.2.1.33.1.2.1.0
    # INTEGER {unknown(1),batteryNormal(2),batteryLow(3),batteryDepleted(4)
    #snmpFolder = 'C:\\Users\\16899486_admin\\Desktop\\C830G\\UPS\\Net-SNMP-Install\\bin\\'
    snmpFolder = '/usr/bin/'
    snmpCMD = [snmpFolder + 'snmpget']
    snmpARG = ['-v', '2c', '-c', 'public', '-OQ', '-t', '10', '-r', '2']
    for str in snmpARG:
        snmpCMD.append(str)

    snmpCMD.append(host.strip())
    snmpCMD.append('.1.3.6.1.2.1.33.1.2.1.0')
    querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
    stdout, stderr = querySNMP.communicate()

    if len(stdout) > 0:
        snmpValue = stdout.decode('utf-8').split('=')[-1].replace('\n', '').strip()
        snmpResults['hostIP'] = host
        if snmpValue == '1' :
            snmpResults['upsBatteryStatus']['status'] = 'unknown'
            snmpResults['upsBatteryStatus']['value'] = snmpValue.strip()
        elif snmpValue == '2' :
            snmpResults['upsBatteryStatus']['status'] = 'batteryNormal'
            snmpResults['upsBatteryStatus']['value'] = snmpValue.strip()
        elif snmpValue == '3' :
            snmpResults['upsBatteryStatus']['status'] = 'batteryLow'
            snmpResults['upsBatteryStatus']['value'] = snmpValue.strip()
        elif snmpValue == '4' :
            snmpResults['upsBatteryStatus']['status'] = 'batteryDepleted'
            snmpResults['upsBatteryStatus']['value'] = snmpValue.strip()             
    elif len(stderr) > 0:
        snmpError = stderr.decode('utf-8').split('=')[-1].replace('\n', '').strip()
        snmpResults['hostIP'] = host
        if 'No Response from' in snmpError:
            snmpResults['upsBatteryStatus']['status'] = 'DOWN/INVALID'
            snmpResults['upsBatteryStatus']['value'] = snmpError.strip()
    return snmpResults

def collectingData(host):
    snmpResults = {
        'hostIP' : None,
        'timeCollected' : secondsTime(),
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
        'upsBatteryStatus' : {
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
    oidToCheck = ['upsBaseBatteryTimeOnBattery','upsSecondsOnBattery','upsSmartInputLineVoltage', 'upsInputVoltage1']
    for eachOIDName, thisDict in snmpMIBS.items(): #name:value pair to fill in the results
        if eachOIDName in oidToCheck:
            #snmpFolder = 'C:\\Users\\16899486_admin\\Desktop\\C830G\\UPS\\Net-SNMP-Install\\bin\\'
            snmpFolder = '/usr/bin/'
            snmpCMD = [snmpFolder + 'snmpget']
            snmpARG = ['-v', '2c', '-c', 'public', '-OQ', '-t', '10', '-r', '2']
            for str in snmpARG:
                snmpCMD.append(str)

            snmpCMD.append(host.strip())
            snmpCMD.append(thisDict['oidString'])
            snmpResults['timeCollected'] = secondsTime()
            querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
            stdout, stderr = querySNMP.communicate()

            if len(stdout) > 0:
                snmpValue = stdout.decode('utf-8').split('=')[-1].replace('\n', '').strip()                
                snmpResults['hostIP'] = host
                if eval (snmpValue.strip() + snmpMIBS[eachOIDName]['expectValue']):
                    snmpResults[eachOIDName]['status'] = 'GOOD'
                    snmpResults[eachOIDName]['value'] = snmpValue.strip()
                else:
                    snmpResults[eachOIDName]['status'] = 'BAD'
                    snmpResults[eachOIDName]['value'] = snmpValue.strip()
            elif len(stderr) > 0:                
                snmpError = stderr.decode('utf-8').split('=')[-1].replace('\n', '').strip()
                snmpResults['hostIP'] = host
                if 'No Response from' in snmpError:
                    snmpResults[eachOIDName]['status'] = 'DOWN/INVALID'
                    snmpResults[eachOIDName]['value'] = snmpError.strip()
    snmpResults = checkBattery(host, snmpResults)
    return snmpResults


def main(hostList):
    listResult = []
    for host in hostList:
        print ('Collecting data from host: ' + host)
        snmpResults = collectingData(host)
        listResult.append(snmpResults)
        time.sleep(1)        
    return listResult


def testFile(filenames = ('good_IP_175.50.44.1.txt', 'bad_IP_175.50.44.1.txt')):
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
    with open('result.json', 'w') as f:
        f.writelines(json.dumps(getAllResuls, indent=4, separators=(", ", " : ")))

if __name__ == '__main__':
    # upsBatteryVoltage  .1.3.6.1.2.1.33.1.2.5  The magnitude of the present battery voltage. keeps decreasing. drop by 50
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

    listResult = main(hostList)

    resultedFile = './statusUPS.json'
    if os.path.isfile(resultedFile):
        if checkLogFileSize(resultedFile):
            with open(resultedFile, 'w+') as f:
                f.writelines(json.dumps(listResult, indent=4, separators=(", ", " : ")))
        else:
            with open(resultedFile, 'a+') as f:
                f.writelines(json.dumps(listResult, indent=4, separators=(", ", " : ")))
