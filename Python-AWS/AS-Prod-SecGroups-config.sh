imageId=$(aws ec2 describe-images --filters "Name=name,Values=autovmprod" --region us-west-1 --query 'Images[*].{ID:ImageId}' | jq '.[] | .ID')
imageId=$(eval echo $imageId)
echo $imageId
if [ -n "$imageId" ] ;then
   aws ec2 deregister-image --image-id $imageId --region us-west-1
fi

instanceId=$(aws elb describe-load-balancers --load-balancer-name prod-ready-staging-balancer --region us-west-1| jq '.LoadBalancerDescriptions | .[] | .Instances | .[0] | .InstanceId')
instanceId=$(eval echo $instanceId)
echo $instanceId
newImageId=$(aws ec2 create-image --instance-id $instanceId --name autovmprod --region us-west-1 --no-reboot | jq '.ImageId')

newImageId=$(eval echo $newImageId)
echo $newImageId

#old Launch configuration for prod-ready-staging-balancer 
old_Prod_Ready=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name Prod_Ready --region us-west-1 | jq '.AutoScalingGroups[] | .LaunchConfigurationName')

#old Launch configuration for www-v2-balancer
old_www_v2=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name www_v2 --region us-west-1 | jq '.AutoScalingGroups[] | .LaunchConfigurationName')


old_Prod_Ready=$(eval echo $old_Prod_Ready)
echo $old_Prod_Ready


old_Prod_Ready=$(eval echo $old_www_v2)
echo $old_www_v2


NOW=$(date +"%s")
#creating new launch configuration for both Autoscaling Groups
new_Prod_Ready="Prod_Ready$NOW"
new_www_v2="www_v2$NOW"



aws autoscaling create-launch-configuration --launch-configuration-name $new_www_v2 --image-id $newImageId --instance-type c4.xlarge --key-name "iss-aws-key-pair-setup" --iam-instance-profile "statamic-role" --security-groups "sg-065170c4e08e4f32a" "sg-e27a7189" "sg-8f65e0e6"  --ebs-optimized --region us-west-1

aws autoscaling create-launch-configuration --launch-configuration-name $new_Prod_Ready --image-id $newImageId --instance-type c4.xlarge --key-name "iss-aws-key-pair-setup" --iam-instance-profile "statamic-role" --security-groups "sg-0ada8db7e78cb4d47" "sg-a1283bd8" "sg-0b5107c46394a3e97" "sg-020d762790743ff89" --ebs-optimized --region us-west-1

#Updating new launch config to the autoscaling groups
aws autoscaling update-auto-scaling-group --auto-scaling-group-name Prod_Ready --launch-configuration-name $new_Prod_Ready --region us-west-1

aws autoscaling update-auto-scaling-group --auto-scaling-group-name www_v2 --launch-configuration-name $new_www_v2 --region us-west-1


#Deleting old launch configuration
aws autoscaling delete-launch-configuration --launch-configuration-name $old_Prod_Ready --region us-west-1

aws autoscaling delete-launch-configuration --launch-configuration-name $old_www_v2 --region us-west-1

