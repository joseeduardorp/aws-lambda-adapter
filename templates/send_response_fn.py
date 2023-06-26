SEND_RESPONSE_FN = """const sendResponse = (
	statusCode: number,
	body: string
): APIGatewayProxyResult => ({
	statusCode,
	body,
	headers: defaultResponseHeaders,
});"""

CALL_FN = "return sendResponse(status_code, body)"
