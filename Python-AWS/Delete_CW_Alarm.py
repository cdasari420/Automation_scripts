from __future__ import print_function
import boto3
import logging

# SNS Topic Definition for EC2, EBS
ec2_sns = 'arn:aws:sns:us-east-2:534484496127:ISS-Ohio-Alarms'


# AWS Account and Region Definition for Reboot Actions
region = 'us-east-2'
name_tag = 'duocom-staging'

# Create AWS clients
ec2session = boto3.client('ec2')
cw = boto3.client('cloudwatch')
ec2 = boto3.resource('ec2')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Retrives instance id from cloudwatch event
def get_instance_id(event):
    try:
        return str(event['detail']['EC2InstanceId'])
    except (TypeError, KeyError) as err:
        LOGGER.error(err)
        return 'instance-id'

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    instanceid = get_instance_id(event)

#Step 1:  Get a list of all alarms in INSUFFICIENT_DATA status
#Step 2:  Get a list of all instances (stopped and started)
#Step 3:  Find all alarms on instances that don't exist, and delete them
###################################################
#Step 1:  Get alarms in INSUFFICENT_DATA state
###################################################
#The max that we can get per loop is 100; all alarms for nonexistent instances will be in
#INSUFFICIENT_DATA state so let's just go through those.
insuff_alarms = []
loops = 1
alarms = cw.describe_alarms(StateValue='INSUFFICIENT_DATA',MaxRecords=100)
#print(alarms)
insuff_alarms.extend(alarms['MetricAlarms'])
while ('NextToken' in alarms):
    alarms = cw.describe_alarms(StateValue='INSUFFICIENT_DATA',MaxRecords=100,NextToken=alarms['NextToken'])
    #print('on loop',loops,'alarms is',alarms)
    insuff_alarms.extend(alarms['MetricAlarms'])
    loops += 1

print('Looped',loops,'times to generate list of ',len(insuff_alarms),'alarms in state INSUFFICIENT_DATA.')
####################################################
#Step 2:  Get all instances
###################################################
#In this case we want all instances.  If an instance is stopped, so be it, we don't delete the alarm.
#But if the instance is gone, then....
#Get all alarms
instances = [instance for instance in ec2.instances.all()]
instance_ids = [instance.id for instance in instances]
print('We have',len(instance_ids),'instances in our account right now.')
#print(instance_ids)

state_dict = {}

for inst in ec2.instances.all():
    state = inst.state['Name']
    if state in state_dict:
        state_dict[state] += 1
    else:
        state_dict[state] = 1
print(state_dict)
###################################################
#Step 3:  Find and delete orphan alarms
###################################################
our_dim = 'InstanceId'
num_orphan_alarms = 0

for insuff_alarm in insuff_alarms:
    #Dimensions is a list of dicts.
    dims = insuff_alarm['Dimensions']
    #print(dim)
    #print(insuff_alarm)
    #print(insuff_alarm,insuff_alarm.namespace,insuff_alarm.dimensions)
    inst_id = ''
    for dim in dims:
        #dim is a dict with two key/values:  Name and Value.  (yes, it's confusing.  Welcome to boto3)
        if dim['Name'] == our_dim:
            inst_id = dim['Value']
    
    if inst_id:
        #this is an instance-level alarm
        #print(insuff_alarm.dimensions)
        if (inst_id not in instance_ids):
            #This is an alarm for an instance that doesn't exist
            name = insuff_alarm['AlarmName']
            print('Alarm',name,"is for an instance that doesn't exist:",inst_id)
            cw.delete_alarms(AlarmNames=[name])
            num_orphan_alarms += 1
    else:
        #print(insuff_alarm.keys())
        print(insuff_alarm['AlarmName'],'has dimensions',dims)

print(num_orphan_alarms,'orphan alarms found and deleted.')