"""
Package definition for Dangerous API rules.
"""

from rules.base.package import RulePackage
from rules.dangerous_api.dynamic_import import DynamicImportRule
from rules.dangerous_api.eval import EvalRule
from rules.dangerous_api.exec import ExecRule
from rules.dangerous_api.marshal_loads import MarshalLoadsRule
from rules.dangerous_api.pickle_loads import PickleLoadsRule
from rules.dangerous_api.reflection import ReflectionRule
from rules.dangerous_api.subprocess_shell import SubprocessShellRule
from rules.dangerous_api.tempfile_mktemp import TempfileMktempRule
from rules.dangerous_api.yaml_load import YamlLoadRule

PACKAGE = RulePackage(
    id="dangerous_api",
    name="Dangerous API Usage",
    version="0.1.0",
    description="Rules targeting insecure API calls, execution functions, and unsafe deserialization.",
    rules=[
        EvalRule,
        ExecRule,
        SubprocessShellRule,
        PickleLoadsRule,
        YamlLoadRule,
        MarshalLoadsRule,
        DynamicImportRule,
        ReflectionRule,
        TempfileMktempRule,
    ],
)
