LAMBDA_IMPORT = "import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';\n"
AUTHORIZER_INTERFACE_IMPORT = (
    "import { AuthorizerUtilsI } from '../interfaces/AuthorizerUtilsTypes';\n"
)
DB_ACTIONS_IMPORTS = "import { DynamoDBI, typed_db_actions } from '../interfaces/DynamoTypes';\n"

TEST_AWS_REQUIRE = "/* istanbul ignore next */\nconst AWS = isTest ? _require('../mocks/AWS').default : _require('aws-sdk');\n"
TEST_DB_REQUIRE = "/* istanbul ignore next */\nconst db: DynamoDBI = isTest ? _require('../mocks/mockedDynamoDB').default : new AWS.DynamoDB.DocumentClient({ region: 'us-west-2' });"
TEST_AUTHORIZER_REQUIRE = "/* istanbul ignore next */\nconst { AuthorizerUtils } = isTest ? _require('../mocks/AuthorizerUtils') : _require('/opt/nodejs/AuthorizerUtils');"
TEST_SENTRY_REQUIRE = "/* istanbul ignore next */\nconst { Sentry, CaptureConsole } = isTest	? _require('../mocks/Sentry')	: _require('/opt/nodejs/Sentry');\n"
