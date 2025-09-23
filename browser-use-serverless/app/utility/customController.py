"""
Example of implementing file upload functionality.

This shows how to upload files to file input elements on web pages.
"""

import asyncio
import logging
import os
import sys

import aiofiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from browser_use import ChatOpenAI
from browser_use.agent.service import Agent, Tools
from browser_use.agent.views import ActionResult
from browser_use.browser import BrowserSession
from browser_use.browser.events import UploadFileEvent
from utility.constants import SESSION_ID_TO_AGENT_MAP
logger = logging.getLogger(__name__)

# Initialize tools
tools = Tools()


@tools.action('Upload file to interactive element with file path')
async def upload_file(index: int, path: str, browser_session: BrowserSession, available_file_paths: list[str]):
	if path not in available_file_paths:
		return ActionResult(error=f'File path {path} is not available')

	if not os.path.exists(path):
		return ActionResult(error=f'File {path} does not exist')

	try:
		# Get the DOM element by index
		dom_element = await browser_session.get_dom_element_by_index(index)

		if dom_element is None:
			msg = f'No element found at index {index}'
			logger.info(msg)
			return ActionResult(error=msg)

		# Check if it's a file input element
		if dom_element.tag_name.lower() != 'input' or dom_element.attributes.get('type') != 'file':
			msg = f'Element at index {index} is not a file input element'
			logger.info(msg)
			return ActionResult(error=msg)

		# Dispatch the upload file event
		event = browser_session.event_bus.dispatch(UploadFileEvent(node=dom_element, file_path=path))
		await event

		msg = f'Successfully uploaded file to index {index}'
		logger.info(msg)
		return ActionResult(extracted_content=msg, include_in_memory=True)

	except Exception as e:
		msg = f'Failed to upload file to index {index}: {str(e)}'
		logger.info(msg)
		return ActionResult(error=msg)
	
@tools.action("Human in the loop")
async def human_in_the_loop(request_id: str,session_id:str,browser_session:BrowserSession) -> ActionResult:
	try:
		agent = SESSION_ID_TO_AGENT_MAP.get(str(session_id))
		print("SESSION_ID_TO_AGENT_MAP:", SESSION_ID_TO_AGENT_MAP)

		if not agent:
			msg = f"No agent found for session_id {session_id}"
			logger.info(msg)
			return ActionResult(error=msg)
		agent.pause()

		msg = f"Agent paused for human intervention on request_id {request_id}, session_id {session_id}. Resume when ready."
		logger.info(msg)

		## call n8n webhook trigger here to notify human the url is http://localhost:5678/webhook/hitl json body as reqeutid sessionid
		import httpx
		webhook_url = os.getenv("HITL_WEBHOOK_URL")
		if not webhook_url:
			msg = "HITL_WEBHOOK_URL is not set in environment variables"
			logger.info(msg)
			return ActionResult(error=msg)
		async with httpx.AsyncClient() as client:
			response = await client.post(webhook_url, json={"request_id": request_id, "session_id": session_id})
			if response.status_code != 200:
				msg = f"Failed to call HITL webhook: {response.status_code} {response.text}"
				logger.info(msg)
				return ActionResult(error=msg)
			else:
				msg = f"Successfully called HITL webhook for request_id {request_id}, session_id {session_id}"
				logger.info(msg)
		return ActionResult(extracted_content=msg, include_in_memory=True)
	except Exception as e:
		msg = f"Error in human_in_the_loop: {str(e)}"
		logger.info(msg)	
		return ActionResult(error=msg)

