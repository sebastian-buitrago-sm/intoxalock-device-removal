from pathlib import Path

from aws_cdk import BundlingOptions, Duration, Stack
from aws_cdk import aws_lambda as _lambda
from constructs import Construct

# infra/stacks/ -> infra/ -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[2]


class LambdaHelloStack(Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # Bundle the app together with its workspace dependency (`core`) by
        # pip-installing both local packages into the Lambda asset. `--no-deps`
        # keeps pip from reaching PyPI for the local `core` requirement.
        bundling = BundlingOptions(
            image=_lambda.Runtime.PYTHON_3_11.bundling_image,
            command=[
                "bash",
                "-c",
                "pip install --no-deps packages/core apps/lambda-hello -t /asset-output",
            ],
        )

        self.function = _lambda.Function(
            self,
            "HelloFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_hello.handler.handler",
            timeout=Duration.seconds(10),
            code=_lambda.Code.from_asset(str(REPO_ROOT), bundling=bundling),
        )
