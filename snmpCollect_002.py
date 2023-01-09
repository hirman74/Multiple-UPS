#!/usr/bin/python3
import os
import json
import time
import socket
from subprocess import Popen, PIPE
# subprocess.run(args, *, stdin=None, input=None, stdout=None, stderr=None, capture_output=False, shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None, text=None, env=None, universal_newlines=None, **other_popen_kwargs)

""" 

SNMP UPS Data Collection

    AC On, Battery On
        upsOutputSource.0 = normal (3)
        upsAlarmsPresent.0 = 0
        upsSecondsOnBattery.0 = 0
        upsEstimatedChargeRemaining.0 = 100
        upsEstimatedMinutesRemaining.0 = 500

    AC On, Battery Off
        upsOutputSource.0 = bypass (4)
        upsAlarmsPresent.0 = 4
        upsAlarmDescr.1 = upsAlarmOnBypass
        upsAlarmDescr.2 = upsAlarmUpsOffAsRequested
        upsAlarmDescr.3 = upsAlarmUpsOutputOff
        upsAlarmDescr.4 = upsAlarmUpsSystemOff
        upsSecondsOnBattery.0 = 0
        upsEstimatedChargeRemaining.0 = 100
        upsEstimatedMinutesRemaining.0 = 500

    AC Off, Battery On
        upsOutputSource.0 = battery (5)
        upsAlarmsPresent.0 = 2
        upsAlarmDescr.1 = upsAlarmOnBattery
        upsAlarmDescr.2 = upsAlarmInputBad
        upsSecondsOnBattery.0 = 188
        upsEstimatedChargeRemaining.0 = 68
        upsEstimatedMinutesRemaining.0 = 497

    Listed SNMP OID
    upsOutputSource
        1.3.6.1.2.1.33.1.4.1
        SYNTAX INTEGER {
            other(1),
            none(2),
            normal(3),
            bypass(4),
            battery(5),
            booster(6),
            reducer(7)
        }
    upsBatteryStatus
        1.3.6.1.2.1.33.1.2.1
        SYNTAX INTEGER {
            unknown(1),
            batteryNormal(2),
            batteryLow(3),
            batteryDepleted(4)
        }
    upsAlarmsPresent
        1.3.6.1.2.1.33.1.6.1
        SYNTAX Gauge32

    upsAlarmDESCR
        1.3.6.1.2.1.33.1.6.5
        SYNTAX DisplayString (SIZE(0..63))
        DESCRIPTION
        "A reference to an alarm description object.  The
        object references should not be accessible, but rather
        be used to provide a unique description of the alarm
        condition."

    upsEstimatedMinutesRemaining
        1.3.6.1.2.1.33.1.2.3
        SYNTAX PositiveInteger
        DESCRIPTION
        "An estimate of the time to battery charge depletion
        under the present load conditions if the utility power
        is off and remains off, or if it were to be lost and
        remain off."

    'mibName' : 'upsInputVoltage1',
    'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.1',
    'expectValue' : ' > 200'

    'mibName' : 'upsInputVoltage2',
    'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.2',
    'expectValue' : ' > 200

    'mibName' : 'upsInputVoltage3',
    'oidString' : '.1.3.6.1.2.1.33.1.3.3.1.3.3',
    'expectValue' : ' > 200'

    upsBatteryVoltage  .1.3.6.1.2.1.33.1.2.5  
    SYNTAX  Gauge32  
    DESCRIPTION  "The magnitude of the present battery voltage."  
    UNITS  "volts"  
    REFERENCE  "UPS-MIB::upsBatteryVoltage"  ::= { upsBatteryEntry 5 }
"""


isAlarm = ['upsBatteryStatus', 'upsAlarmsPresent'] # if any is OR(ZERO) means its Alarm unless is NOT(checkBypass)
isNormalized = ['upsOutputSource', 'upsAlarmsPresent'] # all must be AND(ONE) for normalized 
checkBypass = {'upsMIB' : {'upsOutputSource' : {
                    'mibName' : 'upsOutputSource',
                    'oidString' : '.1.3.6.1.2.1.33.1.4.1.0',
                    'SYNTAX': 'INTEGER',
                    'expectValue' : ' == 4'}}}
checkOnBattery = {'upsMIB' : {'upsOutputSource' : { 
                    'mibName' : 'upsOutputSource',
                    'oidString' : '.1.3.6.1.2.1.33.1.4.1.0',
                    'SYNTAX': 'INTEGER',
                    'expectValue' : ' == 5'}}}
snmpMIBS = {
        'PPC' : {
            'upsBaseBatteryTimeOnBattery': {
                'mibName' : 'upsBaseBatteryTimeOnBattery',
                'oidString' : '.1.3.6.1.4.1.935.1.1.1.2.1.2.0',
                'expectValue' : ' < 60' },
            'upsSmartInputLineVoltage' : {
                'mibName' : 'upsSmartInputLineVoltage',
                'oidString' : '.1.3.6.1.4.1.935.1.1.1.3.2.1.0',
                'expectValue' : ' > 2000' }
                },
        'upsMIB' : {
            'upsOutputSource' : {
                'mibName' : 'upsOutputSource',
                'oidString' : '.1.3.6.1.2.1.33.1.4.1.0',
                'SYNTAX': 'INTEGER',
                'expectValue' : ' == 3',
                'DESCRIPTION' : "The present source of output power. The enumeration none(2) indicates that there is no source of output power (and therefore no output power), for example, the system has opened the output breaker. \
                    other(1), none(2), normal(3), bypass(4), battery(5), booster(6), reducer(7) "},
            'upsBatteryStatus' : {
                'mibName' : 'upsBatteryStatus',
                'oidString' : '.1.3.6.1.2.1.33.1.2.1.0',
                'SYNTAX': 'INTEGER',
                'expectValue' : ' == 2',
                'DESCRIPTION' : 'The indication of the capacity remaining in the UPS systems batteries. \
                    A value of batteryNormal(2) indicates that the remaining run-time is greater than upsConfigLowBattTime. \
                    A value of batteryLow(3) indicates that the remaining battery run-time is less than or equal to upsConfigLowBattTime. \
                    A value of batteryDepleted(4) indicates that the UPS will be unable to sustain the present load when \
                    and if the utility power is lost (including the possibility that the utility power is currently absent and the UPS is unable to sustain the output). \
                    unknown(1), batteryNormal(2), batteryLow(3), batteryDepleted(4)'},
            'upsSecondsOnBattery' : {
                'mibName' : 'upsSecondsOnBattery',
                'oidString' : '.1.3.6.1.2.1.33.1.2.2.0',
                'SYNTAX': 'NonNegativeInteger',
                'expectValue' : ' == 0',
                'DESCRIPTION' : 'If the unit is on battery power, the elapsed time since the UPS last switched to battery power, \
                    or the time since the network management subsystem was last restarted, whichever is less. \
                    Zero shall be returned if the unit is not on battery power.'},
            'upsEstimatedMinutesRemaining' : {
                'mibName' : 'upsEstimatedMinutesRemaining',
                'oidString' : '.1.3.6.1.2.1.33.1.2.3.0',
                'SYNTAX': 'PositiveInteger',
                'expectValue' : ' > 60',
                'DESCRIPTION' : 'An estimate of the time to battery charge depletion under the present load conditions if the utility power is off and remains off, or if it were to be lost and remain off.'},            
            'upsEstimatedChargeRemaining' : {
                'mibName' : 'upsEstimatedChargeRemaining',
                'oidString' : '.1.3.6.1.2.1.33.1.2.4',
                'SYNTAX': 'INTEGER (0..100)',
                'expectValue' : ' > 50',
                'DESCRIPTION' : 'An estimate of the battery charge remaining expressed as a percent of full charge.'},
            'upsAlarmsPresent': {
                'mibName' : 'upsAlarmsPresent',
                'oidString' : '.1.3.6.1.2.1.33.1.6.1.0',
                'SYNTAX': 'Gauge32',
                'expectValue' : ' == 0',
                'DESCRIPTION' : 'The present number of active alarm conditions.'}
            }
    }


resultFile = 'statusUPS.json'
keepRecords = 1000000000000

def getGlobalString ():
    timedOutSeconds = '5'
    retryCount = '3'
    # snmpFolder = '/usr/bin/'
    snmpFolder = 'C:\\Users\\16899486_admin\\Desktop\\C830G\\UPS\\Net-SNMP-Install\\bin\\'
    snmpCMD = [snmpFolder + 'snmpget']
    snmpARG = ['-v', '2c', '-c', 'public', '-OQ', '-t', timedOutSeconds, '-r', retryCount]
    return snmpARG, snmpCMD

def secondsTime():
    getHourMinuteSeconds = time.strftime("%Y%b%d_%H%M%S")
    return getHourMinuteSeconds

def checkLogFileSize(resultFile):
    if os.path.getsize(resultFile) > 1000:
        return True

def getAlarmState(host):    
    collectValues = []
    collectResults = []
    for eachOIDName in isAlarm:
        getOIDString = snmpMIBS['upsMIB'][eachOIDName]['oidString']
        snmpARG, snmpCMD = getGlobalString ()
        for str in snmpARG:
            snmpCMD.append(str)
        snmpCMD.append(host.strip())
        snmpCMD.append(getOIDString)

        #print ('getAlarmState' , ' ', snmpCMD)
        querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
        stdout, stderr = querySNMP.communicate()

        if len(stdout) > 0: 
            #print ('getAlarmState' , ' ', stdout)
            snmpValue = stdout.decode('utf-8').split('=')[-1].replace('\n', '').strip()
            print ('getAlarmState' , ' ', snmpValue, ' ', snmpMIBS['upsMIB'][eachOIDName]['expectValue'])
            if eval (snmpValue.strip() + snmpMIBS['upsMIB'][eachOIDName]['expectValue']):
                collectResults.append(1) ## Passed the expectValue
                collectValues.append(snmpValue.strip())
            else:
                collectResults.append(0) ## Failed the expectValue
        elif len(stderr) > 0: 
            #print ('getAlarmState' , ' ', stderr)
            snmpError = stderr.decode('utf-8').split('=')[-1].replace('\n', '').strip()
            #print ('getAlarmState' , ' ', snmpError)
            if 'No Response from' in snmpError:
                collectResults.append(0) ## Failed the expectValue
                collectValues.append(snmpError.strip())
    if 0 in collectResults:
        return ('isAlarm')
    else:
        return ('isNormal')

def getNormalizedState(host):
    collectValues = []
    collectResults = []
    for eachOIDName in isNormalized:
        getOIDString = snmpMIBS['upsMIB'][eachOIDName]['oidString']
        snmpARG, snmpCMD = getGlobalString ()
        for str in snmpARG:
            snmpCMD.append(str)
        snmpCMD.append(host.strip())
        snmpCMD.append(getOIDString)

        print ('getNormalizedState', ' ', snmpCMD)
        querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
        stdout, stderr = querySNMP.communicate()

        if len(stdout) > 0: 
            print ('getNormalizedState', ' ', stdout)
            snmpValue = stdout.decode('utf-8').split('=')[-1].replace('\n', '').strip()
            #print ('getNormalizedState', ' ', snmpValue)
            if eval (snmpValue.strip() + snmpMIBS['upsMIB'][eachOIDName]['expectValue']):
                collectResults.append(1) ## Passed the expectValue
                collectValues.append(snmpValue.strip())
            else:
                collectResults.append(0) ## Failed the expectValue
        elif len(stderr) > 0: 
            print ('getNormalizedState', ' ', stderr)
            snmpError = stderr.decode('utf-8').split('=')[-1].replace('\n', '').strip()
            #print ('getNormalizedState', ' ', snmpError)
            if 'No Response from' in snmpError:
                collectResults.append(0) ## Failed the expectValue
                collectValues.append(snmpError.strip())
    if 0 in collectResults:
        return ('isAlarm')
    else:
        return ('isNormal')

def isBypass(host):
    getOIDString = checkBypass['upsMIB']['upsOutputSource']['oidString']
    snmpARG, snmpCMD = getGlobalString ()
    for str in snmpARG:
        snmpCMD.append(str)
    snmpCMD.append(host.strip())
    snmpCMD.append(getOIDString)
    #print ('isBypass', ' ', snmpCMD)
    querySNMP = Popen( snmpCMD , stdout=PIPE, stderr=PIPE)
    
    stdout, stderr = querySNMP.communicate()
    #print ('isBypass', ' ', stdout)

    if len(stdout) > 0: 
        snmpValue = stdout.decode('utf-8').split('=')[-1].replace('\n', '').strip()
        #print ('isBypass', ' ', snmpValue)
        if eval (snmpValue.strip() + checkBypass['upsMIB']['upsOutputSource']['expectValue']):
            return 'isBypass'
        elif eval (snmpValue.strip() + snmpMIBS['upsMIB']['upsOutputSource']['expectValue']):
            return 'notBypass'

def eachHost(host):
    eachResult = {'result' : None, 'time' : None }        
    print ('Collecting data from host: ' + host)
    if isBypass(host) == 'isBypass':
        eachResult['result'] = 'isBypass'
        eachResult['time'] = str(time.strftime("%Y%b%d_%H%M%S"))
        return eachResult       
    elif getAlarmState(host) == 'isAlarm':
        eachResult['result'] = 'isAlarm'
        eachResult['time'] = str(time.strftime("%Y%b%d_%H%M%S"))
        return eachResult                   
    elif getNormalizedState(host) == 'isNormal':
        eachResult['result'] = 'isNormal'
        eachResult['time'] = str(time.strftime("%Y%b%d_%H%M%S"))
        return eachResult

def getLocation():
    if '-' in socket.gethostname():
        thisHostname = socket.gethostname().split('-')
    elif '_' in socket.gethostname():
        thisHostname = socket.gethostname().split('_')
    for locName in thisHostname:
        if locName.upper() in ('MFT', 'SMS', 'UPS', 'RTU', 'FEP', 'PLC', '0', '1', '2'):  
            continue
        return 'UPS-'+ locName + '-1', 'UPS-'+ locName + '-2'

def getJSONfile(hostList, resultFile):
    backupJSON = {}
    if os.path.isfile(resultFile):
        with open(resultFile, 'r') as f:
            jsonString = json.loads(f.read())
            for host in hostList:
                eachResult = eachHost(host)
                if host in jsonString:
                    backupJSON[host] = jsonString[host]
                    backupJSON[host].append(eachResult)
                else:
                    backupJSON[host] = []
                    backupJSON[host].append(eachResult)            
                while(len(backupJSON[host]) > keepRecords):
                    backupJSON[host].pop(0)
    else:
        for host in hostList:
            eachResult = eachHost(host)
            backupJSON[host] = []
            backupJSON[host].append(eachResult)            
            while(len(backupJSON[host]) > keepRecords):
                backupJSON[host].pop(0)
    return backupJSON

if __name__ == '__main__':
    hostList = ['175.50.44.1']
    # hostList = getLocation()
    while True:        
        jsonString = getJSONfile(hostList, resultFile)
        with open(resultFile, 'w+') as f:
            f.writelines(json.dumps(jsonString, indent=4, separators=(", ", " : ")))
        time.sleep(10)

