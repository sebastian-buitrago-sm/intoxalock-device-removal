import aws_cdk as cdk
from stacks.lambda_hello import LambdaHelloStack

app = cdk.App()

# All infrastructure for every app in the monorepo is declared here.
LambdaHelloStack(app, "LambdaHelloStack")

app.synth()
