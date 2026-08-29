"""
Package definition for Injection rules.
"""

from rules.base.package import RulePackage
from rules.injection.command_injection import CommandInjectionRule
from rules.injection.ldap_injection import LdapInjectionRule
from rules.injection.nosql_injection import NosqlInjectionRule
from rules.injection.sql_format import SqlFormatRule
from rules.injection.sql_fstring import SqlFstringRule
from rules.injection.sql_percent_format import SqlPercentFormatRule
from rules.injection.sql_string_concat import SqlStringConcatRule

PACKAGE = RulePackage(
    id="injection",
    name="Injection Vulnerabilities",
    version="0.1.0",
    description="Rules targeting SQL, Command, NoSQL, and LDAP injection flaws.",
    rules=[
        SqlStringConcatRule,
        SqlFstringRule,
        SqlFormatRule,
        SqlPercentFormatRule,
        CommandInjectionRule,
        NosqlInjectionRule,
        LdapInjectionRule,
    ],
)
