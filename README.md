deploy-button :ship: :red_circle:
======

CodePipeline supports Manual Approval actions that allow you to put manual gates in your pipeline. IoT Buttons allow you to have a real world button hooked up to a Lambda function. This project configures your IoT button to approve (or reject) your CodePipeline manual approval steps.

What's in the box
------

The `deploy-button` project utilizes several AWS services to get things working. 

* CodePipeline:
  *  Sample Pipeline
* SNS Topics:
  * Manual Approvals
  * Button presses
* Lambda Functions:
  * Save Approval Token
  * Approve/Deny
* SSM Parameter: 
  * Approval Token
* IoT:
  * Thing
  * Policy
  * Rule
  * Certificate

Workflow:
------
After you've run the CloudFormation templates to create everything, the pipeline will execute and the follow steps will occur:
* Code Pipeline Hits Manual Action
* It generates SNS notification
* Lambda Receives SNS notification and saves approval token (ssm)

Once the pipeline stops at the approval action, your IoT button can accept or reject the changes by either long pressing (accept) or short pressing (deny) the button.
* Button generates SNS notification
* Lambda Receives SNS notification and looks up approval token
* Lambda calls code Pipeline API with approval token


Commands:
-----
This will get easier someday.

    # need to input these manually for now
    export iot_button_dsn=1234567890
    export cert_arn=arn:aws:iot:us-east-1:1234567890:cert/123456abcdef7890

    aws cloudformation create-stack \
      --stack-name "test-ssm-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/ssm.yml

    sns_stack_name="test-sns-$(date +%Y%m%d%H%M%S)"
    aws cloudformation create-stack \
      --stack-name $sns_stack_name \
      --template-body file://provisioning/sns.yml \
      --capabilities CAPABILITY_IAM

    # wait for sns stack to complete

      aws cloudformation create-stack \
      --stack-name "test-iot-button-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/iotbutton.yml \
      --capabilities CAPABILITY_IAM \
      --region us-east-1 \
      --parameters \
        ParameterKey="ButtonListenerTopic",ParameterValue="$(aws cloudformation describe-stacks --stack-name $sns_stack_name --query Stacks[*].Outputs[?OutputKey==\'ButtonListenerTopic\'].OutputValue --output text)" \
        ParameterKey="ButtonListenerTopicRoleARN",ParameterValue="$(aws cloudformation describe-stacks --stack-name $sns_stack_name --query Stacks[*].Outputs[?OutputKey==\'ButtonListenerTopicRole\'].OutputValue --output text)" \
        ParameterKey="IoTButtonDSN",ParameterValue="$iot_button_dsn" \
        ParameterKey="CertificateARN",ParameterValue="$cert_arn" 
