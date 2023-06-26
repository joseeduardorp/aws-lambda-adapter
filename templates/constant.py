IS_TEST = "/* istanbul ignore next */\nconst isTest: boolean = process.env.JEST_WORKER_ID ? true : false;\n"
REQUIRE = "/* istanbul ignore next */\nconst _require: any = isTest\n? require\n: //@ts-ignore\n __non_webpack_require__;\n"
SENTRY = (
    "/* istanbul ignore next */\nif (!isTest) {\n/* istanbul ignore next */\nsentry_instance\n};"
)

# handler's
HANDLER_TYPED = (
    "exports.handler = async (e: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {"
)
HANDLER_SENTRY_TYPED = "exports.handler = Sentry.AWSLambda.wrapHandler(async (e: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {"
HANDLER_TEST = "const index = async (e: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {"
HANDLER_SENTRY_EXPORT = "\n/* istanbul ignore next */\nexport const handler = isTest ? index : Sentry.AWSLambda.wrapHandler(index);\n"
HANDLER_EXPORT = "\n/* istanbul ignore next */\nexport const handler = index;\n"
