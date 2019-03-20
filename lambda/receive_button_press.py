import json
import httplib
import logging
from urllib2 import build_opener, HTTPHandler, Request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info('REQUEST RECEIVED:\n {}'.format(event))
    logger.info('REQUEST RECEIVED:\n {}'.format(context))
    # this will need to be un-hardcoded at some point
    pipelineName = 'SamplePipelinewithManualStep'
    response = client.get_pipeline_state(
        name=pipelineName
    )

    # is there any way these can be dynamically looked up?
    # maybe if we require certain names for the stage & action?
    token = response['stageStates'][1]['actionStates'][1]['latestExecution']['token']
    logger.info('token:\t {}'.format(token))
    stageName = response['stageStates'][1]['stageName']
    logger.info('stage:\t {}'.format(stageName))
    actionName = response['stageStates'][1]['actionStates'][1]['actionName']
    logger.info('action:\t {}'.format(actionName))

    response = client.put_approval_result(
        pipelineName=pipelineName,
        stageName=stageName,
        actionName=actionName,
        result={
            'summary': 'Approved via IOT Button Press',
            'status': 'Approved'
        },
        token=token
    )
    logger.info('response:\n {}'.format(response))


def sendResponse(event, context, responseStatus, responseData):
    responseBody = json.dumps({
        "Status": responseStatus,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": responseData
    })

    logger.info('ResponseURL: {}'.format(event['ResponseURL']))
    logger.info('ResponseBody: {}'.format(responseBody))

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=responseBody)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(responseBody))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    print("Status code: {}".format(response.getcode()))
    print("Status message: {}".format(response.msg))
