TEST = """//@ts-ignore
import { expect, describe, it } from '@jest/globals';

//@ts-ignore
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

//@ts-ignore
import { handler } from '../index';
//@ts-ignore
import { mockedAuthValues } from '../../mocks/AuthorizerUtils';
import mockedDynamoDB, {
	successfulDeleteOperation,
	successfulGetOperation,
	successfulPutOperation,
	successfulQueryOperation,
	successfulUpdateOperation,
} from '../../mocks/mockedDynamoDB';
//@ts-ignore
import { GetParamsI } from '../../interfaces/DynamoTypes';

const resetMockedDynamoDB = (): void => {
	mockedDynamoDB.get = successfulGetOperation;
	mockedDynamoDB.query = successfulQueryOperation;
	mockedDynamoDB.update = successfulUpdateOperation;
	mockedDynamoDB.delete = successfulDeleteOperation;
	mockedDynamoDB.put = successfulPutOperation;
};

describe('function_name handler', () => {
	beforeEach(() => {
		resetMockedDynamoDB();
	});
});"""
