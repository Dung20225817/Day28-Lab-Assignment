import inspect
from prefect.deployments import RunnerDeployment
sig = inspect.signature(RunnerDeployment.from_flow)
for name, param in sig.parameters.items():
    if 'job' in name.lower() or 'infra' in name.lower():
        ann = param.annotation
        ann_name = getattr(ann, '__name__', str(ann))
        print(f'{name}: {ann_name} = {param.default}')
