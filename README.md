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
First you have to configure the IoT button to connect to your AWS account. This is done by create keys and certificates that you'll need to upload to the button. First we'll create the keys and certs:

    # first thing: generate IOT cert
    aws iot create-keys-and-certificate --set-as-active --output json > keys-and-cert.json
    export cert_arn=$(cat keys-and-cert.json | jq '.certificateArn' | tr -d '"')
    cat keys-and-cert.json | jq '.certificatePem' | tr -d '"' | awk '{gsub(/\\n/,"\n")}1' > certificate.pem
    cat keys-and-cert.json | jq '.keyPair.PrivateKey' | tr -d '"' | awk '{gsub(/\\n/,"\n")}1' > private.key
    rm keys-and-cert.json

You'll also want to run these two commands and note the output:
    aws iot describe-endpoint | jq .endpointAddress | tr -d '"' | awk -F. '{ print $1}'
    aws iot describe-endpoint | jq .endpointAddress | tr -d '"' | awk -F. '{ print $3}'

Next is the annoying bit: the IoT button is configured by connecting to it's wireless network and pulling up a webpage. You'll need to put the IoT button into configuration mode, connect to it from your computer, and then enter in the appropriate information.
1. Hold down the IoT button for 10 seconds, until the light begins flashing blue.
2. A wireless network will appear, named something like `Button-ConfigureMe`, connect to it.
3. Navigate to http://192.168.0.1/index.html
4. Enter your wifi information -- *note*: if you're on a network that configures wifi via a redirect, you won't be able to use your IoT button.
5. Under `AWS IoT Configuration`
  * For `Certificate` upload the file you created above `certificate.pem`
  * For `Private Key` uploaded the file you created above `private.key`
  * For `Endpoint Subdomain` enter the output from the first command above.
  * For `Region`, enter the output from the second command above.
 6. Check the agreement to terms and conditions box
 7. Click `Configure`
 8. Reconnect to your nomal wireless network.

Now that the IoT button is configured, we can set up the resources to support it. You'll need to set the values of the first two variables.


    # The DSN will be on the back of your IoT button
    export iot_button_dsn=1234567890
    # this can be whatever you like, leaving it as is should work too.
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
