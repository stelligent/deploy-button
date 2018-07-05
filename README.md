deploy-button :ship: :red_circle:
======

CodePipeline supports Manual Approval actions that allow you to put manual gates in your pipeline. IoT Buttons allow you to have a real world button hooked up to a Lambda function. This project configures your IoT button to approve (or reject) your CodePipeline manual approval steps.

*This is currently a work in progress; nothing actually is working right now.*

What's in the box
------

The `deploy-button` project utilizes several AWS services to get things working. 

* CodePipeline:
  *  Sample Pipeline
* SNS Topics:
  * Manual Approvals
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
    export lambda_bucket=test-lambda-functions-$(date +%Y%m%d%H%M%S)

    aws cloudformation create-stack \
      --stack-name "test-ssm-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/ssm.yml

    sns_stack_name="test-sns-$(date +%Y%m%d%H%M%S)"
    aws cloudformation create-stack \
      --stack-name $sns_stack_name \
      --template-body file://provisioning/sns.yml \
      --capabilities CAPABILITY_IAM

    # put lambda functions into S3 so the CloudFormation stacks can find them
    pushd lambda
      aws s3 mb s3://${lambda_bucket}
      rm -rf tmp
      mkdir -p tmp
      zip tmp/receive_button_press.zip receive_button_press.py
      zip tmp/receive_manual_approval.zip receive_manual_approval.py
      aws s3 cp tmp/receive_button_press.zip s3://${lambda_bucket}/receive_button_press.zip
      aws s3 cp tmp/receive_manual_approval.zip s3://${lambda_bucket}/receive_manual_approval.zip
      rm -rf tmp
    popd

    lambdas_stack_name=test-lambdas-$(date +%Y%m%d%H%M%S)
    aws cloudformation create-stack \
      --stack-name "$lambdas_stack_name" \
      --template-body file://provisioning/lambdas.yml \
      --capabilities CAPABILITY_IAM \
      --disable-rollback \
      --parameters \
        ParameterKey="SourceBucket",ParameterValue="${lambda_bucket}" \
        ParameterKey="ReceiveButtonPressZip",ParameterValue="receive_button_press.zip" \
        ParameterKey="ReceiveManualApprovalNotificationZip",ParameterValue="receive_manual_approval.zip"
    # wait for lambda stack to complete, about 30s
    sleep 60

    aws cloudformation create-stack \
      --stack-name "test-iot-button-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/iotbutton.yml \
      --capabilities CAPABILITY_IAM \
      --region us-east-1 \
      --parameters \
        ParameterKey="IoTButtonDSN",ParameterValue="$iot_button_dsn" \
        ParameterKey="CertificateARN",ParameterValue="$cert_arn" \
        ParameterKey="ButtonListenerLambdaArn",ParameterValue="$(aws cloudformation describe-stacks --stack-name $lambdas_stack_name --query Stacks[*].Outputs[?OutputKey==\'ButtonListenerLambdaArn\'].OutputValue --output text)"
