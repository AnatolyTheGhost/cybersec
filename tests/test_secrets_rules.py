import unittest

from modules.ast.builder import ASTBuilder
from modules.semantic_ast.builder import SemanticBuilder
from engine.context import AnalysisContext
from rules.secrets.aws_key import AwsKeyRule
from rules.secrets.azure_key import AzureKeyRule
from rules.secrets.bearer_token import BearerTokenRule
from rules.secrets.connection_string import ConnectionStringRule
from rules.secrets.database_credentials import DatabaseCredentialsRule
from rules.secrets.discord_token import DiscordTokenRule
from rules.secrets.dotenv_file import DotenvFileRule
from rules.secrets.github_token import GithubTokenRule
from rules.secrets.gitlab_token import GitlabTokenRule
from rules.secrets.hardcoded_password import HardcodedPasswordRule
from rules.secrets.jwt_secret import JwtSecretRule
from rules.secrets.mongodb_credentials import MongodbCredentialsRule
from rules.secrets.oauth_token import OauthTokenRule
from rules.secrets.openai_key import OpenaiKeyRule
from rules.secrets.pem_key import PemKeyRule
from rules.secrets.private_key import PrivateKeyRule
from rules.secrets.redis_credentials import RedisCredentialsRule
from rules.secrets.rsa_key import RsaKeyRule
from rules.secrets.slack_token import SlackTokenRule
from rules.secrets.smtp_credentials import SmtpCredentialsRule
from rules.secrets.ssh_key import SshKeyRule
from rules.secrets.stripe_key import StripeKeyRule
from rules.secrets.telegram_token import TelegramTokenRule


class SecretsRuleTestCase(unittest.TestCase):
    def _make_context(self, source: str):
        ast_tree = ASTBuilder().build(source, file_path="sample.py")
        semantic_ast = SemanticBuilder().build(ast_tree, filename="sample.py")
        return AnalysisContext(source_code=source, file_path="sample.py", semantic_ast=semantic_ast)

    def test_all_secret_rules_emit_findings(self):
        cases = [
            (AwsKeyRule(), 'AWS_ACCESS_KEY_ID = "AKIA1234567890ABCD"\nAWS_SECRET_ACCESS_KEY = "abcd1234efgh5678"'),
            (AzureKeyRule(), 'AZURE_CLIENT_SECRET = "secret-value"\nAZURE_STORAGE_KEY = "abc123"'),
            (BearerTokenRule(), 'auth_header = "Bearer abcdefghijklmnop"'),
            (ConnectionStringRule(), 'DATABASE_URL = "postgresql://user:pass@localhost/db"'),
            (DatabaseCredentialsRule(), 'DB_PASS = "supersecret"\nDB_USER = "root"'),
            (DiscordTokenRule(), 'DISCORD_TOKEN = "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI"'),
            (DotenvFileRule(), 'dotenv_path = ".env"'),
            (GithubTokenRule(), 'token = "ghp_abcdefghijklmnopqrstuv"'),
            (GitlabTokenRule(), 'token = "glpat-abcdefghijklmnopqrstuv"'),
            (HardcodedPasswordRule(), 'password = "hunter2"'),
            (JwtSecretRule(), 'JWT_SECRET = "super-secret-jwt-key"'),
            (MongodbCredentialsRule(), 'MONGO_URI = "mongodb://user:pass@host/db"'),
            (OauthTokenRule(), 'OAUTH_TOKEN = "oauth-secret-token"'),
            (OpenaiKeyRule(), 'OPENAI_API_KEY = "sk-1234567890abcdefghijklmnopqrst"'),
            (PemKeyRule(), 'key = "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----"'),
            (PrivateKeyRule(), 'key = "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----"'),
            (RedisCredentialsRule(), 'REDIS_URL = "redis://user:pass@localhost:6379/0"'),
            (RsaKeyRule(), 'key = "-----BEGIN RSA PRIVATE KEY-----\\nabc\\n-----END RSA PRIVATE KEY-----"'),
            (SlackTokenRule(), 'SLACK_TOKEN = "xoxb-123456789012-123456789012-abcdefghijklmnopqrstuv"'),
            (SmtpCredentialsRule(), 'SMTP_PASSWORD = "mailpass"'),
            (SshKeyRule(), 'key = "-----BEGIN OPENSSH PRIVATE KEY-----\\nabc\\n-----END OPENSSH PRIVATE KEY-----"'),
            (StripeKeyRule(), 'STRIPE_SECRET_KEY = "sk_live_1234567890abcdefghijklmnopqrst"'),
            (TelegramTokenRule(), 'BOT_TOKEN = "123456789:abcdefghijklmnopqrstuv"'),
        ]

        for rule, source in cases:
            with self.subTest(rule=rule.__class__.__name__):
                context = self._make_context(source)
                findings = rule.analyze(context)
                self.assertGreater(len(findings), 0, f"{rule.__class__.__name__} should detect a secret")


if __name__ == "__main__":
    unittest.main()
