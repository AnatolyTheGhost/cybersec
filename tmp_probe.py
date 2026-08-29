import os
import sys
sys.path.insert(0, r'c:/Users/Anatolii/Documents/Cybersec')
from engine.context import AnalysisContext
from engine.pipelines.secrets import SecretsPipeline
from engine.pipelines.injection import InjectionPipeline
from engine.pipelines.dangerous_api import DangerousApiPipeline
from engine.pipelines.authorization import AuthorizationPipeline

ctx = AnalysisContext(source_code='x=1\n', workspace_path='.')
for pipeline_cls in [SecretsPipeline, InjectionPipeline, DangerousApiPipeline, AuthorizationPipeline]:
    try:
        pipeline = pipeline_cls()
        pipeline.execute('.', context=ctx, workspace_path='.')
        print(pipeline_cls.__name__, 'OK')
    except Exception as e:
        print(pipeline_cls.__name__, type(e).__name__, e)
