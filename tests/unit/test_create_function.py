import pytest
import unittest
from unittest.mock import MagicMock
from aws_lambda.aws_lambda import create_function


class TestFunctionCreation(object):
    @pytest.fixture
    def setEnv(self, mocker):
        mocker.patch.dict('os.environ', {
            'S3_BUCKET_NAME': 'testBucket',
            'LAMBDA_FUNCTION_NAME': 'testFunc'
        })

    @pytest.fixture
    def cfgDict(self):
        return {
            'profile': 'testAWSProfile',
            'aws_access_key_id': 'testKey',
            'aws_secret_access_key': 'testSecret',
            'region': 'testRegion',
            'handler': 'test.py',
            'runtime': 'testPython',
        }

    @pytest.fixture
    def kwargDict(self):
        return {
            'FunctionName': 'testFunc',
            'Runtime': 'testPython',
            'Role': 'testRole',
            'Handler': 'test.py',
            'Code': {'ZipFile': 'bytes'},
            'Description': '',
            'Timeout': 15,
            'MemorySize': 512,
            'VpcConfig': {'SubnetIds': [], 'SecurityGroupIds': []},
            'Publish': True
        }

    @pytest.fixture
    def commonMocks(self, mocker):
        mocker.patch('aws_lambda.aws_lambda.read', return_value='bytes')
        mocker.patch('aws_lambda.aws_lambda.get_account_id')
        mocker.patch(
            'aws_lambda.aws_lambda.get_role_name',
            return_value='testRole'
        )

    @pytest.fixture
    def mockClient(self, mocker):
        mockClient = MagicMock()
        mocker.patch(
            'aws_lambda.aws_lambda.get_client',
            return_value=mockClient
        )
        return mockClient

    def test_basicCreation(self, mocker, setEnv, cfgDict, kwargDict,
                           commonMocks, mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=0)

        create_function(cfgDict, 'testPath')

        mockClient.create_function.assert_called_with(**kwargDict)
        assert not mockClient.put_function_concurrency.called

    def test_creationWithSubnetSecurity(self, mocker, setEnv, cfgDict,
                                        kwargDict, commonMocks, mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=0)
        cfgDict['subnet_ids'] = 'sub1, sub2'
        cfgDict['security_group_ids'] = 'group1, group2'
        kwargDict['VpcConfig']['SubnetIds'] = ['sub1', 'sub2']
        kwargDict['VpcConfig']['SecurityGroupIds'] = ['group1', 'group2']

        create_function(cfgDict, 'testPath')
        mockClient.create_function.assert_called_with(**kwargDict)
        assert not mockClient.put_function_concurrency.called

    def test_s3Creation(self, mocker, setEnv, cfgDict, kwargDict, commonMocks,
                        mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=0)
        kwargDict['Code'] = {
            'S3Bucket': 'testBucket',
            'S3Key': 'testFile'
        }

        create_function(cfgDict, 'testPath', use_s3=True, s3_file='testFile')
        mockClient.create_function.assert_called_with(**kwargDict)
        assert not mockClient.put_function_concurrency.called

    def test_createWithConcurrency(self, mocker, setEnv, cfgDict, kwargDict,
                                   commonMocks, mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=1)

        create_function(cfgDict, 'testPath')
        mockClient.create_function.assert_called_with(**kwargDict)
        mockClient.put_function_concurrency.assert_called_with(**{
            'FunctionName': 'testFunc',
            'ReservedConcurrentExecutions': 1
        })

    def test_createWithTags(self, mocker, setEnv, cfgDict, kwargDict,
                            commonMocks, mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=0)

        cfgDict['tags'] = {
            'test': 'test'
        }

        kwargDict['Tags'] = {
            'test': 'test'
        }

        create_function(cfgDict, 'testPath')
        mockClient.create_function.assert_called_with(**kwargDict)
        assert not mockClient.put_function_concurrency.called

    def test_createWithEnvVars(self, mocker, setEnv, cfgDict, kwargDict,
                               commonMocks, mockClient):
        mocker.patch('aws_lambda.aws_lambda.get_concurrency', return_value=0)
        mocker.patch(
            'aws_lambda.aws_lambda.get_environment_variable_value',
            side_effect=[1, 'testing']
        )
        cfgDict['environment_variables'] = {
            'numVar': '1',
            'txtVar': 'testing'
        }

        kwargDict['Environment'] = {
            'Variables': {
                'numVar': 1,
                'txtVar': 'testing'
            }
        }

        create_function(cfgDict, 'testPath')
        mockClient.create_function.assert_called_with(**kwargDict)
        assert not mockClient.put_function_concurrency.called


if __name__ == '__main__':
    unittest.main()
