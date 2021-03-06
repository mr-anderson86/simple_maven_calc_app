#!/usr/bin/python

import sys
import json
import urllib2
import csv
import traceback

#--------------------------------------------------------------------
##=Name         get_job_details.py
##
##=Purpose      get Jenkins Job details from jenkins job api and calculate to human readable time
##
##=Parameters
##              1. jenkinsURL - the jenkins url which we will take the data from. for example: http://jenkins.server:8080, MANDATORY param
##              2. jenkinsJob - the jenkins job name which we will take the data from. for example: calc_ci_cd, MANDATORY param
##              3. buildNum - the build number which we will take the data from. default value is lastBuild.  OPTIONAL param
##                                        parameter examples:
##                                        lastCompletedBuild, lastFailedBuild, lastStableBuild, lastSuccessfulBuild, lastUnstableBuild, lastUnsuccessfulBuild
##
##=Examples
##      python get_job_details.py http://jenkins.server:8080 calc_ci_cd
##          python get_job_details.py://jenkins.server:8080 calc_ci_cd 1102
##              python get_job_details.py http://jenkins.server:8080 calc_ci_cd lastSuccessfulBuild


def init(argv):
        if len(argv) == 4 :
                jenkinsURL = sys.argv[1]
                jobName = sys.argv[2]
                buildNum = sys.argv[3]
        elif len(argv) == 3 :
                jenkinsURL = sys.argv[1]
                jobName = sys.argv[2]
                buildNum = 'lastBuild'
        else:
                # print sys.argv
                sys.exit(1)

        return {'jenkinsURL':jenkinsURL, 'jobName':jobName ,'buildNum':buildNum }

        # DEBUG: jenkins URL and job name
        # print "jenkinsURL : " + str( jenkinsURL )
        # print "jobName : " + str( jobName )


def getJsonFromJenkinsApi(jenkinsURL, jobName, buildNum):
        link=jenkinsURL + "/job/" + jobName + "/" + buildNum + "/api/json"
        try:
                # loading jenkins job api URL
                # DEBUG: print jenkins URL
                # print "Jenkins URL : " + str( link )
                linkStream   = urllib2.urlopen( link )

        except urllib2.HTTPError, e:
                print "URL Error: " + str(e.code)
                print "      (job name [" + jobName + "] probably wrong)"
                traceback.print_exc()
                sys.exit(2)

        try:
                jsonData = json.load( linkStream )
                # DEBUG: print json generated from jenkins job api
                # print json.dumps(jsonData, indent=1)
                return jsonData

        except:
                # print "Failed to parse json"
                sys.exit(3)


def getKeyFromJenkinsApi(jsonData, keyName):
    # find in json the needed key - Jenkins Node and get its value
    if jsonData.has_key(keyName):
        lastBuildServerName = jsonData[keyName]
        return lastBuildServerName
    else:
        #No such key in json...
        # print "Error: No such key " + keyName
        # sys.exit(5)
        return "NA"


def getJobStartedBy(jsonData):
    for action in jsonData['actions']:
        if action.has_key('causes'):
            # print action
            for cause in action['causes']:
                if cause.has_key('userName'):
                    return cause['userName'].replace(" ", "_")
                elif cause.has_key('upstreamProject'):
                    return cause['upstreamProject']
                elif cause.has_key('shortDescription'):
                    return cause['shortDescription']
                else:
                    return "NA"


def calculateDuration(durationInSec):
    if durationInSec == "NA":
        return "NA"
    # convert milliseconds to human readble time - hours minutes seconds
    millis = int(durationInSec)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24

    # add left zero if needed - only if one digit
    if len(str(seconds)) == 1:
        seconds = '0' + str(seconds)

    if len(str(minutes)) == 1:
        minutes = '0' + str(minutes)

    if len(str(hours)) == 1:
        hours = '0' + str(hours)

    # two options for output - textual and clock - clock is activated
    # print "Took " + str( hours ) + " hours " + str( minutes ) + " min " + str( seconds ) + " sec"
    buildDuration = str(hours) + ":" + str(minutes) + ":" + str(seconds)
    return buildDuration


# -------------------------------------------------------------------
# --           M A I N   S E C T I O N                             --
# -------------------------------------------------------------------


def main(argv):
        funcValues = init(argv)
        jobJsonData = getJsonFromJenkinsApi(funcValues['jenkinsURL'], funcValues['jobName'], funcValues['buildNum'])
        jobSlave = getKeyFromJenkinsApi(jobJsonData, "builtOn")
        jobBuildStatus = ""
        if jobJsonData["building"]:
            jobBuildStatus = "building"
        else:
            jobBuildStatus = getKeyFromJenkinsApi(jobJsonData, "result")

        jobStartedBy = getJobStartedBy(jobJsonData)
        jobDuration = getKeyFromJenkinsApi(jobJsonData, "duration")
        jobDuration = str(jobDuration).replace('\r\n', '')
        jobDuration = calculateDuration(jobDuration)

        print("Job name: " + funcValues['jobName'])
        print("Build num: " + funcValues['buildNum'])
        print("Started by: " + jobStartedBy)
        print("Status:" + jobBuildStatus)
        print("Duration:" + jobDuration)
        print("Slave: " +  jobSlave)
        
        csv_file_name = funcValues['jobName'] + '_' + funcValues['buildNum'] + '.csv'
        with open(csv_file_name,'wb') as csvfile:
            fieldnames=['Field', 'Value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'Field': 'Job name:' , 'Value': funcValues['jobName']})
            writer.writerow({'Field': 'Build num:' , 'Value': funcValues['buildNum']})
            writer.writerow({'Field': 'Started by:' , 'Value': jobStartedBy})
            writer.writerow({'Field': 'Status:' , 'Value': jobBuildStatus})
            writer.writerow({'Field': 'Duration:' , 'Value': jobDuration})
            writer.writerow({'Field': 'Slave:' , 'Value': jobSlave})

        print("Generated CSV file at your location: "+ csv_file_name)

        sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
