imageId=$(aws ec2 describe-images --filters "Name=name,Values=autovmstaging" --region us-east-2 --query 'Images[*].{ID:ImageId}' | jq '.[] | .ID')
imageId=$(eval echo $imageId)
echo $imageId
if [ -n "$imageId" ] ;then
   aws ec2 deregister-image --image-id $imageId --region us-east-2
fi

instanceId=$(aws elb describe-load-balancers --load-balancer-name www-staging-a --region us-east-2 | jq '.LoadBalancerDescriptions | .[] | .Instances | .[0] | .InstanceId')
instanceId=$(eval echo $instanceId)
echo $instanceId
newImageId=$(aws ec2 create-image --instance-id $instanceId --name autovmstaging --region us-east-2 --no-reboot | jq '.ImageId')

newImageId=$(eval echo $newImageId)
echo $newImageId

old_launchConfig=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name Autoscale_Staging --region us-east-2 | jq '.AutoScalingGroups[] | .LaunchConfigurationName')

old_launchConfig=$(eval echo $old_launchConfig)
echo $old_launchConfig

NOW=$(date +"%s")
new_launchConfig="Staginglaunch$NOW"

aws autoscaling create-launch-configuration --launch-configuration-name $new_launchConfig --image-id $newImageId --instance-type c4.xlarge --key-name "iss-aws-key-pair-setup" --iam-instance-profile "statamic-role" --security-groups "sg-065170c4e08e4f32a" "sg-e27a7189" "sg-8f65e0e6"  --ebs-optimized --region us-east-2
aws autoscaling update-auto-scaling-group --auto-scaling-group-name Autoscale_Staging --launch-configuration-name $new_launchConfig --region us-east-2
aws autoscaling update-auto-scaling-group --auto-scaling-group-name Autoscale_Staging_ready --launch-configuration-name $new_launchConfig --region us-east-2
aws autoscaling delete-launch-configuration --launch-configuration-name $old_launchConfig --region us-east-2
