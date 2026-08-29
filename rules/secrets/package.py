"""
Package definition for Secrets rules.
"""

from rules.base.package import RulePackage
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

PACKAGE = RulePackage(
    id="secrets",
    name="Hardcoded Secrets Detection",
    version="0.1.0",
    description="Rules targeting API keys, database credentials, tokens, passwords, and private keys.",
    rules=[
        AwsKeyRule,
        AzureKeyRule,
        GithubTokenRule,
        GitlabTokenRule,
        OpenaiKeyRule,
        StripeKeyRule,
        SlackTokenRule,
        DiscordTokenRule,
        TelegramTokenRule,
        JwtSecretRule,
        BearerTokenRule,
        OauthTokenRule,
        HardcodedPasswordRule,
        DatabaseCredentialsRule,
        SmtpCredentialsRule,
        RedisCredentialsRule,
        MongodbCredentialsRule,
        PrivateKeyRule,
        RsaKeyRule,
        SshKeyRule,
        PemKeyRule,
        ConnectionStringRule,
        DotenvFileRule,
    ],
)
