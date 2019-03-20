import json
import httplib
import logging
from urllib2 import build_opener, HTTPHandler, Request
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info('REQUEST RECEIVED:\n {}'.format(event))
    logger.info('REQUEST RECEIVED:\n {}'.format(context))
    # this will need to be un-hardcoded at some point
    pipelineName = 'SamplePipelinewithManualStep'
    client = boto3.client('codepipeline')
    response = client.get_pipeline_state(
        name=pipelineName
    )

    # is there any way these can be dynamically looked up?
    # maybe if we require certain names for the stage & action?
    token = response['stageStates'][1]['actionStates'][0]['latestExecution']['token']
    logger.info('token:\t {}'.format(token))
    stageName = response['stageStates'][1]['stageName']
    logger.info('stage:\t {}'.format(stageName))
    actionName = response['stageStates'][1]['actionStates'][0]['actionName']
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
