"""
Package definition for Authorization rules.
"""

from rules.authorization.idor import IdorRule
from rules.authorization.missing_authentication import MissingAuthenticationRule
from rules.authorization.missing_authorization import MissingAuthorizationRule
from rules.authorization.missing_owner_check import MissingOwnerCheckRule
from rules.authorization.missing_permission_check import MissingPermissionCheckRule
from rules.authorization.missing_role_check import MissingRoleCheckRule
from rules.authorization.privilege_escalation import PrivilegeEscalationRule
from rules.authorization.public_admin_endpoint import PublicAdminEndpointRule
from rules.authorization.unprotected_sensitive_operation import (
    UnprotectedSensitiveOperationRule,
)
from rules.base.package import RulePackage

PACKAGE = RulePackage(
    id="authorization",
    name="Authorization & Access Control",
    version="0.1.0",
    description="Rules targeting missing authentication, access control issues, IDOR, and privilege escalation.",
    rules=[
        MissingAuthenticationRule,
        MissingAuthorizationRule,
        MissingRoleCheckRule,
        MissingPermissionCheckRule,
        MissingOwnerCheckRule,
        IdorRule,
        PrivilegeEscalationRule,
        PublicAdminEndpointRule,
        UnprotectedSensitiveOperationRule,
    ],
)
