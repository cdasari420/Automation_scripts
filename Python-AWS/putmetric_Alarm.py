from __future__ import print_function
import boto3
import logging

# SNS Topic Definition for EC2, EBS
ec2_sns = 'arn:aws:sns:us-east-2:534484496127:ISS-Ohio-Alarms'
ebs_sns = 'arn:aws:sns:us-east-2:534484496127:ISS-Ohio-Alarms'

# AWS Account and Region Definition for Reboot Actions
akid = 'AKIAIORC6NHQZVHCHIYQ'
region = 'us-east-2'
name_tag = 'Staging'

# Create AWS clients
ec2session = boto3.client('ec2')
cw = boto3.client('cloudwatch')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Retrives instance id from cloudwatch event
def get_instance_id(event):
    try:
        return event['detail']['EC2InstanceId']
    except KeyError as err:
        LOGGER.error(err)
        return 'instanceid not found'

def lambda_handler(event, context):

    session = boto3.session.Session()
    ec2session = session.client('ec2')
    instanceid = get_instance_id(event)

    # Create Metric "CPU Utilization Greater than 75% for 5 Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s High CPU Utilization Warning" % (name_tag, instanceid),
    AlarmDescription='CPU Utilization Greater than 75% for 5 Minutes',
    ActionsEnabled=True,
    OKActions=[
        ec2_sns
    ],
    AlarmActions=[
        ec2_sns
    ],
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=300,
    EvaluationPeriods=1,
    Threshold=75.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

# Create Metric "Status Check Failed (System) for 1 Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s System Check Failed" % (name_tag, instanceid),
    AlarmDescription='Status Check Failed (System) for 1 Minutes',
    ActionsEnabled=True,
    OKActions=[
        ec2_sns
    ],
    AlarmActions=[
        ec2_sns,
        "arn:aws:automate:%s:ec2:recover" % region
    ],
    MetricName='StatusCheckFailed_System',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=60,
    EvaluationPeriods=2,
    Threshold=1.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

