#!/usr/bin/env python
import sys
import boto3
ec2 = boto3.resource('ec2')
for instance_id in sys.argv[1:]:
    instance = ec2.Instance(i-004941fc5966f252b)
    response = instance.terminate()
    print response
