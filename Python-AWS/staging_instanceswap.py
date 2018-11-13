import boto3
import sys
import string
import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('region')
    parser.add_argument('staging_elb_name')
    parser.add_argument('staging_ready_elb_name')

    args = parser.parse_args()

    elb = boto3.client('elb', region_name = args.region)
    ec2 = boto3.resource('ec2', region_name = args.region)

    # checking to make sure we are executing in the correct region. Should be us-east-2 since that is where staging duo.com is.
    if args.region != 'us-east-2':
        print("Error. This is not the region duo.com staging exists in.")
        sys.exit()

    # getting list of instances in staging elb. getting list of instances in staging_ready elb
    staging_ready_ips = get_instances_in_elb(elb, args.staging_elb_name)
    if not staging_ready_ips:
        print("Error. There are no instances in the {} load balancer.".format(args.staging_elb_name))
        sys.exit()
    else:
	staging_ready_ips = get_instances_in_elb(elb, args.staging_ready_elb_name)

    # if there are instances in the staging_ready elb deregister them from the staging_ready load balancer.
    if not staging_ready_ips:
        print("Error. There are no instances in the {} load balancer".format(args.staging_ready_elb_name))
        sys.exit()
    else:
	for instance_id in staging_ready_ips:
            deregister_instances(elb, args.staging_ready_elb_name, instance_id)

    # check to make sure staging_ready elb is empty. If it is, assign staging security groups to staging_ready instances
    empty_staging = get_instances_in_elb(elb, args.staging_ready_elb_name)
    if not empty_staging:
        print("All instances have been removed from {} elb successfully".format(args.staging_ready_elb_name))
        staging_ready_security_groups = get_security_groups(ec2, staging_ready_ips[0])
        staging_security_groups = get_security_groups(ec2, staging_ready_ips[0])
        if not staging_ready_security_groups or not staging_security_groups:
            print("Error. Somehow the security groups are empty..")
        else:
            update_security_groups(ec2, staging_ready_ips, staging_security_groups)
    else:
	print("Error. There are still instances in {} load balancer.".format(args.staging_ready_elb_name))
        sys.exit()

    # checking security groups before placing the staging_ready instances into staging elb. Register staging_ready instances into staging$
    healthy_staging_instances = set()
    for staging_ready_ip in staging_ready_ips:
        if check_security_groups(ec2, staging_security_groups, staging_ready_ip) != staging_ready_ip:
            print("Security Groups are not set up properly for {} load balancer.".format(args.staging_elb_name))
            sys.exit()
        else:
            print("{} is ready for {} elb".format(staging_ready_ip, args.staging_elb_name))
            if register_instances(elb, args.staging_elb_name, staging_ready_ip) != staging_ready_ip:
                print("something went really wrong")
                sys.exit()
            else:
                health = check_instance_inservice(elb, staging_ready_ip, args.staging_elb_name)
                if health is not False:
                    healthy_staging_instances.add(staging_ready_ip)
                    print(healthy_staging_instances)
                are_all_staging_instances_in_staging = [x for x in staging_ready_ips if x not in healthy_staging_instances]
                if not are_all_staging_instances_in_staging:
                    print("all instances from {} elb have been added to {} elb".format(args.staging_ready_elb_name, args.staging_elb_name$))
                    for staging_ip in staging_ready_ips:
                        # before I remove these instances should i make sure i am getting a response from the ELB/CDN origin?
                        deregister_instances(elb, args.staging_elb_name, staging_ip)
                else:
                    print("not all instances from {} elb have been added to {} elb".format(args.staging_ready_elb_name, args.staging_elb_name$))

    # make sure now old staging instances are removed from staging elb. update security groups to be placed in staging_ready elb
    new_staging_instances = get_instances_in_elb(elb, args.staging_elb_name)
    now_old_staging_ips = set(staging_ready_ips)
    are_old_staging_ips_removed = [x for x in now_old_staging_ips if x not in new_staging_instances]
    if not are_old_staging_ips_removed:
        print("Not all old instances have been removed from the {} load balancer".format(args.staging_elb_name))
    else:
    print("{} instances have successfully been removed from the {} load balancer".format(are_old_staging_ips_removed, args.staging_elb_name$))
        update_security_groups(ec2, staging_ready_ips, staging_ready_security_groups)

    # check security groups before placing staging instances into staging_ready elb. Register staging instances into staging_ready and en$
    healthy_staging_ready_instances = set()
    for staging_ip in staging_ready_ips:
        if check_security_groups(ec2, staging_ready_security_groups, staging_ip) != staging_ip:
            print("Security groups are not set up properly for {} load balancer.".format(args.staging_ready_elb_name))
        else:
            print("{} is ready for {} elb".format(staging_ip, args.staging_ready_elb_name))
            if register_instances(elb, args.staging_ready_elb_name, staging_ip) != staging_ip:
                print("{} instance was not added to {} load balancer".format(staging_ip, args.staging_ready_elb_name))
            else:
                instance_health = check_instance_inservice(elb, staging_ip, args.staging_ready_elb_name)
                if instance_health is not False:
                    healthy_staging_ready_instances.add(staging_ip)
                    print(staging_ip)
                are_all_staging_instances_in_staging_ready = [x for x in staging_ready_ips if x not in healthy_staging_ready_instances]
                if not are_all_staging_instances_in_staging_ready:
                    print("all instances from {} load balancer have been added into {} load balancer".format(args.staging_elb_name$))
                else:
                    print("not all instances in {} elb have been added to {} elb".format(args.staging_elb_name, args.staging_elb$))
def get_instances_in_elb(elb, elb_name):
    all_load_balancers = elb.describe_load_balancers()
    for elbs in all_load_balancers['LoadBalancerDescriptions']:
        load_balancer_names = elbs['LoadBalancerName']
        if elb_name == load_balancer_names:
            ec2_in_elb = elbs['Instances']
            ec2_in_elb = [x['InstanceId'] for x in ec2_in_elb]
            return ec2_in_elb

def deregister_instances(elb, elb_name, instance_id):
    elb.deregister_instances_from_load_balancer(LoadBalancerName=elb_name, Instances=[{'InstanceId': instance_id}])
    print("Removed {} from {} load balancer".format(instance_id, elb_name))

def get_security_groups(ec2, instance_id):
    all_instances = ec2.instances.filter()
    for instance in all_instances:
        if instance.id == instance_id:
            security_groups = [sg['GroupId'] for sg in instance.security_groups]
            return security_groups

def update_security_groups(ec2, instances, security_groups):
    all_instances = ec2.instances.filter()
    for instance in all_instances:
        for instance_id in instances:
            if instance.id == instance_id:
                instance.modify_attribute(Groups = security_groups)
                new_security_groups = [sg['GroupId'] for sg in instance.security_groups]
                print("{} instance now has {} security groups".format(instance_id, new_security_groups))

def check_security_groups(ec2, new_security_groups, instance_id):
    all_instances = ec2.instances.filter()
    for instance in all_instances:
        if instance.id == instance_id:
            security_groups = [sg['GroupId'] for sg in instance.security_groups]
            new_security_groups = set(new_security_groups)
            are_they_different = [x for x in security_groups if x not in new_security_groups]
            if not are_they_different:
                return instance_id
            else:
                print("The security groups attached to the staging instances are not ready for production")

def register_instances(elb, elb_name, instance_id):
    elb.register_instances_with_load_balancer(LoadBalancerName=elb_name, Instances=[{'InstanceId': instance_id}])
    print("{} instance has been added to {} load balancer".format(instance_id, elb_name))
    return instance_id

# checks that the instance is in service in the elb before moving on
def check_instance_inservice(elb, instance_id, elb_name):
    is_instance_healthy = False
    retries = 0
    while retries < 30 and not is_instance_healthy:
        instance_health = True
        response = elb.describe_instance_health(LoadBalancerName=elb_name, Instances=[{'InstanceId': instance_id}])
        elb_instances_health = response['InstanceStates']
        for instance in elb_instances_health:
            current_instance_in_service = instance['State'] == 'InService'
            instance_health = instance_health and current_instance_in_service
        if instance_health is not False:
            print("Instance {} is healthy and in {} load balancer".format(instance_id, elb_name))
            is_instance_healthy = True
            break
        time.sleep(7)
        retries = retries + 1
    return is_instance_healthy


if __name__ == "__main__":
    main()
