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
